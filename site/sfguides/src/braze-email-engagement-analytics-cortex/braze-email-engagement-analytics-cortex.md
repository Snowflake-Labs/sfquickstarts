author: Snowflake
id: braze-email-engagement-analytics-cortex
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration
language: en
summary: Analyze Braze email engagement data and product reviews with Snowflake Cortex AI for campaign optimization, personalization, and marketing insights.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues

# AI-Powered Campaign Analytics with Braze and Snowflake Cortex

## Overview

In this hands-on lab, you'll build an intelligent marketing analytics solution that combines Braze email engagement data with product reviews using Snowflake's Cortex AI capabilities. You'll create a natural language interface through Snowflake Intelligence that allows marketers to query both structured campaign performance data and unstructured customer reviews to receive AI-powered insights and recommendations.

## About Braze

Braze is a Customer Engagement Platform used to power personalized, real-time marketing communications across every touchpoint, including email, push notifications, in-app messages, SMS, and WhatsApp. The platform captures a rich stream of first-party data, such as detailed user profiles, message engagement metrics (sends, opens, clicks), and custom behavioral events like purchases or conversions.

By centralizing this granular engagement data in Snowflake, you can join it with other business data to build a comprehensive 360-degree customer view. This enables deeper analytics on user behavior, more sophisticated customer segmentation, and the ability to power data-driven personalization. 

Fundamentally, combining Braze and Snowflake allows you to fully understand the total business impact of your marketing workflows, campaigns and interactions across the ecosystem.


### What You'll Learn
- How to set up Snowflake environment for Braze engagement data and product reviews
- How to create a Semantic View for structured data analysis with Cortex Analyst
- How to create a Cortex Search Service for unstructured product review analysis
- How to use Snowflake Intelligence to query both structured and unstructured data

### What You'll Build
- A complete data pipeline for Braze email engagement data and product reviews
- A Semantic View that enables natural language queries on structured campaign data
- A Cortex Search Service for semantic search on product reviews (RAG)
- A Snowflake Intelligence agent that combines both tools for comprehensive marketing insights

### Prerequisites
- Basic familiarity with SQL
- Access to Snowflake account with Cortex enabled
- Understanding of email marketing concepts

## Environment Setup

First, let's prepare your Snowflake environment and enable cross-region LLM usage.

### Enable Cross-Region Cortex Access

Run the following command in a SQL worksheet to enable cross-region usage of LLMs, as your current region may be limited in which LLMs it can use:

```sql
ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';
```

### Create Database and Schema

Run the following SQL commands in a SQL worksheet to create the warehouse, database and schema:

```sql
-- create the database
CREATE OR REPLACE DATABASE BRAZE_ENGAGEMENT;

-- create the schema
CREATE SCHEMA BRAZE_ENGAGEMENT.EMAIL_DATA;

-- switch to database and schema that was created
USE DATABASE BRAZE_ENGAGEMENT;
USE SCHEMA EMAIL_DATA;

-- create stage for raw data
CREATE OR REPLACE STAGE EMAIL_STAGE DIRECTORY = (ENABLE = TRUE);
```

## Create Data Tables

Now we'll create tables for your email engagement data, campaign changelog data, and product reviews. The full table schemas for Braze engagement data can be found [here](https://www.braze.com/docs/assets/download_file/data-sharing-raw-table-schemas.txt?dadd92e90dc27e8a5066e9eea327c65e).

You will be prompted to download the files shortly from GDRIVE or an AWS bucket.

Positive
: **Note on Data Types**: For this lab, we're using `TIMESTAMP_LTZ` datatype rather than a Number representing a UNIX timestamp for easier use in setting up our semantic view.

Run the following SQL to create all necessary tables:

```sql
-- create the table to hold our changelog data
CREATE OR REPLACE TABLE CAMPAIGN_CHANGELOGS (
    ID VARCHAR(16777216),
    TIME NUMBER(38,0),
    APP_GROUP_ID VARCHAR(16777216),
    API_ID VARCHAR(16777216) PRIMARY KEY,
    NAME VARCHAR(16777216),
    CONVERSION_BEHAVIORS ARRAY,
    ACTIONS ARRAY
);

-- create the table to hold our email send data
CREATE OR REPLACE TABLE EMAIL_SENDS (
    ID VARCHAR(16777216) PRIMARY KEY,
    USER_ID VARCHAR(16777216),
    EXTERNAL_USER_ID VARCHAR(16777216),
    DEVICE_ID VARCHAR(16777216),
    APP_GROUP_ID VARCHAR(16777216),
    APP_GROUP_API_ID VARCHAR(16777216),
    TIME TIMESTAMP_LTZ(9),
    DISPATCH_ID VARCHAR(16777216),
    SEND_ID VARCHAR(16777216),
    CAMPAIGN_ID VARCHAR(16777216),
    CAMPAIGN_API_ID VARCHAR(16777216),
    MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_ID VARCHAR(16777216),
    CANVAS_API_ID VARCHAR(16777216),
    CANVAS_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_STEP_API_ID VARCHAR(16777216),
    CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    GENDER VARCHAR(16777216),
    COUNTRY VARCHAR(16777216),
    TIMEZONE VARCHAR(16777216),
    LANGUAGE VARCHAR(16777216),
    EMAIL_ADDRESS VARCHAR(16777216),
    IP_POOL VARCHAR(16777216),
    MESSAGE_EXTRAS VARCHAR(16777216),
    ESP VARCHAR(16777216),
    FROM_DOMAIN VARCHAR(16777216),
    SF_CREATED_AT TIMESTAMP_LTZ(9)
);

-- create the table to hold our email open data
CREATE OR REPLACE TABLE EMAIL_OPENS (
    ID VARCHAR(16777216),
    USER_ID VARCHAR(16777216),
    EXTERNAL_USER_ID VARCHAR(16777216),
    DEVICE_ID VARCHAR(16777216),
    APP_GROUP_ID VARCHAR(16777216),
    APP_GROUP_API_ID VARCHAR(16777216),
    TIME TIMESTAMP_LTZ(9),
    DISPATCH_ID VARCHAR(16777216),
    SEND_ID VARCHAR(16777216),
    CAMPAIGN_ID VARCHAR(16777216),
    CAMPAIGN_API_ID VARCHAR(16777216),
    MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_ID VARCHAR(16777216),
    CANVAS_API_ID VARCHAR(16777216),
    CANVAS_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_STEP_API_ID VARCHAR(16777216),
    CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    GENDER VARCHAR(16777216),
    COUNTRY VARCHAR(16777216),
    TIMEZONE VARCHAR(16777216),
    LANGUAGE VARCHAR(16777216),
    EMAIL_ADDRESS VARCHAR(16777216),
    USER_AGENT VARCHAR(16777216),
    IP_POOL VARCHAR(16777216),
    MACHINE_OPEN VARCHAR(16777216),
    ESP VARCHAR(16777216),
    FROM_DOMAIN VARCHAR(16777216),
    IS_AMP BOOLEAN,
    SF_CREATED_AT TIMESTAMP_LTZ(9),
    PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
);

-- create the table to hold our email click data
CREATE OR REPLACE TABLE EMAIL_CLICKS (
    ID VARCHAR(16777216),
    USER_ID VARCHAR(16777216),
    EXTERNAL_USER_ID VARCHAR(16777216),
    DEVICE_ID VARCHAR(16777216),
    APP_GROUP_ID VARCHAR(16777216),
    APP_GROUP_API_ID VARCHAR(16777216),
    TIME TIMESTAMP_LTZ(9),
    DISPATCH_ID VARCHAR(16777216),
    SEND_ID VARCHAR(16777216),
    CAMPAIGN_ID VARCHAR(16777216),
    CAMPAIGN_API_ID VARCHAR(16777216),
    MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_ID VARCHAR(16777216),
    CANVAS_API_ID VARCHAR(16777216),
    CANVAS_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_STEP_API_ID VARCHAR(16777216),
    CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    GENDER VARCHAR(16777216),
    COUNTRY VARCHAR(16777216),
    TIMEZONE VARCHAR(16777216),
    LANGUAGE VARCHAR(16777216),
    EMAIL_ADDRESS VARCHAR(16777216),
    URL VARCHAR(16777216),
    USER_AGENT VARCHAR(16777216),
    IP_POOL VARCHAR(16777216),
    LINK_ID VARCHAR(16777216),
    LINK_ALIAS VARCHAR(16777216),
    MACHINE_OPEN VARCHAR(16777216),
    ESP VARCHAR(16777216),
    FROM_DOMAIN VARCHAR(16777216),
    IS_AMP BOOLEAN,
    SF_CREATED_AT TIMESTAMP_LTZ(9),
    PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
);

-- create the table to hold our email unsubscribe data
CREATE OR REPLACE TABLE EMAIL_UNSUBSCRIBES (
    ID VARCHAR(16777216),
    USER_ID VARCHAR(16777216),
    EXTERNAL_USER_ID VARCHAR(16777216),
    DEVICE_ID VARCHAR(16777216),
    APP_GROUP_ID VARCHAR(16777216),
    APP_GROUP_API_ID VARCHAR(16777216),
    TIME TIMESTAMP_LTZ(9),
    DISPATCH_ID VARCHAR(16777216),
    SEND_ID VARCHAR(16777216),
    CAMPAIGN_ID VARCHAR(16777216),
    CAMPAIGN_API_ID VARCHAR(16777216),
    MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_ID VARCHAR(16777216),
    CANVAS_API_ID VARCHAR(16777216),
    CANVAS_VARIATION_API_ID VARCHAR(16777216),
    CANVAS_STEP_API_ID VARCHAR(16777216),
    CANVAS_STEP_MESSAGE_VARIATION_API_ID VARCHAR(16777216),
    GENDER VARCHAR(16777216),
    COUNTRY VARCHAR(16777216),
    TIMEZONE VARCHAR(16777216),
    LANGUAGE VARCHAR(16777216),
    EMAIL_ADDRESS VARCHAR(16777216),
    IP_POOL VARCHAR(16777216),
    SF_CREATED_AT TIMESTAMP_LTZ(9),
    PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
);

-- create the table to hold product reviews for RAG analysis
CREATE OR REPLACE TABLE PRODUCT_REVIEWS (
    REVIEW_ID VARCHAR(50) PRIMARY KEY,
    USER_ID VARCHAR(50),
    RATING NUMBER(1,0),
    REVIEW_TEXT VARCHAR(16777216),
    PRODUCT_SENTIMENT VARCHAR(20),
    REVIEW_DATE DATE,
    PURCHASE_LOCATION VARCHAR(50),
    PRODUCT_CATEGORY VARCHAR(100),
    ITEM_NAME VARCHAR(200)
);
```

After running this SQL, navigate to **Data** > **Databases** and you should see your BRAZE_ENGAGEMENT database, EMAIL_DATA schema, and the 6 tables you just created.

## Upload Sample Data

Now we'll upload sample CSV files to populate our tables with demo data.

### Download Sample Files

Download the following CSV files (also available through the AWS bucket provided):

- [USERS_MESSAGES_EMAIL_UNSUBSCRIBE_VIEW.csv](https://drive.google.com/file/d/18UVrQtTiKxjeuvZGjSevQqsf4Tvos-oe/view?usp=sharing)
- [USERS_MESSAGES_EMAIL_CLICK_VIEW.csv](https://drive.google.com/file/d/1J-q5QXGfcXqaHeAuRbx5xZP5NFAHVsnq/view?usp=sharing)
- [USERS_MESSAGES_EMAIL_OPEN_VIEW.csv](https://drive.google.com/file/d/1flPAmYxc5GDAE39C7AfxDoxJO3hGFtJg/view?usp=sharing)
- [USERS_MESSAGES_EMAIL_SEND_VIEW.csv](https://drive.google.com/file/d/10IJVJ57RymlVodGQZOHXznDddx28sYBy/view?usp=sharing)
- [CHANGELOGS_CAMPAIGN_VIEW.csv](https://drive.google.com/file/d/1bh7hC__TMH52pmqnH2ZAEUA19AsC5Q7r/view?usp=sharing)

Positive
: **Note**: Product reviews data will be inserted directly via SQL in the next section, so no CSV upload is required for that table.

### Upload Files to Stage

To upload the data files:

1. Choose **Create** in the left-hand navigation and select **Add Data** from the dropdown
2. On the Add Data page, select **Load files into a stage**
3. Select the five Braze CSV files that you want to upload (listed above)
4. Select BRAZE_ENGAGEMENT as Database, EMAIL_DATA as Schema, and EMAIL_STAGE as Stage
5. Click **Upload**

Navigate to **Data > Databases**, click into your BRAZE_ENGAGEMENT Database, EMAIL_DATA Schema, and the EMAIL_STAGE. You should see your 5 files listed.

## Load Data into Tables

Now we'll load the data from your CSV files into their respective tables. Run the following SQL against the BRAZE_ENGAGEMENT database:

```sql
USE DATABASE BRAZE_ENGAGEMENT;
USE SCHEMA EMAIL_DATA;

-- load data into changelog 
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."CAMPAIGN_CHANGELOGS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('CHANGELOGS_CAMPAIGN_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- Insert product reviews data directly
INSERT INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."PRODUCT_REVIEWS" 
    (REVIEW_ID, USER_ID, RATING, REVIEW_TEXT, PRODUCT_SENTIMENT, REVIEW_DATE, PURCHASE_LOCATION, PRODUCT_CATEGORY, ITEM_NAME)
VALUES
    ('R-1001', '06Y1ResADlZutwm', 5, 'The denim jeans fit perfectly and the quality is exceptional for the price. I wish I had bought two pairs!', 'Positive', '2026-03-01', 'Retail Store', 'Apparel', 'Denim Jeans'),
    ('R-1002', '0MJWsStTQuYWYq7', 1, 'My coffee maker stopped working after the first week. Customer service was unhelpful and the return process is lengthy.', 'Negative', '2026-03-02', 'Online', 'Home Goods', 'Coffee Maker'),
    ('R-1003', '1NQHFvWpLpo5LkC', 4, 'Love these wireless earbuds! Great sound for the price, though the charging case feels a little cheap.', 'Positive', '2026-03-03', 'App', 'Electronics', 'Wireless Earbuds'),
    ('R-1004', '1N6R4EtkRuKEjFP', 3, 'The travel guide was adequate, but definitely focused on tourist traps. Could have found better information online.', 'Neutral', '2026-03-04', 'Retail Store', 'Books', 'Travel Guide'),
    ('R-1005', '1OEy7FFzL9n5FTl', 5, 'Gorgeous leather belt. High quality leather and the buckle looks very classy. Fast shipping too!', 'Positive', '2026-03-05', 'Online', 'Accessories', 'Leather Belt'),
    ('R-1006', '09cW2jhmIPQ6CZ8', 2, 'The Desk Organizer was broken upon arrival. The plastic is very brittle. Disappointed with the packaging.', 'Negative', '2026-03-06', 'Retail Store', 'Office Supplies', 'Desk Organizer'),
    ('R-1007', '0PCkfnjde7Pz7Ya', 5, 'This portable charger is a lifesaver. Holds multiple charges and is surprisingly slim. Five stars!', 'Positive', '2026-03-07', 'App', 'Electronics', 'Portable Charger'),
    ('R-1008', '1kQ6yr6aL53RiIi', 4, 'Great comfy throw pillow, but the colour online was slightly different than in person. Still keeping it.', 'Positive', '2026-03-08', 'Online', 'Home Goods', 'Throw Pillow'),
    ('R-1009', '1rBWPEkCfELrJvN', 1, 'The blouse I ordered was completely mis-sized. Their sizing chart is inaccurate. Painful return.', 'Negative', '2026-03-09', 'Retail Store', 'Apparel', 'Women''s Blouse'),
    ('R-1010', '1CiXHH9esPaVbPD', 5, 'Fantastic graphic novel! Gripping story and beautiful artwork. I finished it in one sitting.', 'Positive', '2026-03-10', 'Online', 'Books', 'Graphic Novel'),
    ('R-1011', '2TJbTSzVuzOLCyV', 3, 'The Ballpoint Pen Set is okay. They write smoothly, but the ink runs out very quickly. Average performance.', 'Neutral', '2026-03-11', 'App', 'Office Supplies', 'Ballpoint Pen Set'),
    ('R-1012', '1nr0Sc7qqc11Yvs', 5, 'The smartwatch is incredible. Battery lasts for days, and the fitness tracking is spot-on.', 'Positive', '2026-03-12', 'Retail Store', 'Electronics', 'Smartwatch'),
    ('R-1013', '1wVK1lM7ubrkm2X', 4, 'Very stylish sunglasses. They feel durable and the lens clarity is excellent.', 'Positive', '2026-03-13', 'Online', 'Accessories', 'Sunglasses'),
    ('R-1014', '0qQjEmXLdgz60m4', 2, 'Received the wrong colour sweater. Tried to exchange it at the store, but they were sold out. Frustrating.', 'Negative', '2026-03-14', 'Retail Store', 'Apparel', 'Wool Sweater'),
    ('R-1015', '1FSTUNOW1Rvxm9x', 5, 'The bestseller novel was a phenomenal read! A true page-turner. Highly recommend this author.', 'Positive', '2026-03-15', 'Online', 'Books', 'Bestseller Novel'),
    ('R-1016', '0aAwdB6llYxSJTf', 3, 'The kettle is functional, but it''s much louder than my previous one. Neutral experience overall.', 'Neutral', '2026-03-16', 'App', 'Home Goods', 'Electric Kettle'),
    ('R-1017', '0y1lStmktDkJe2V', 1, 'The store layout was confusing and the staff seemed more interested in talking amongst themselves.', 'Negative', '2026-03-17', 'Retail Store', 'Accessories', 'Handbag'),
    ('R-1018', '0xzqZ2V5su9JSBj', 5, 'Perfect set of noise-cancelling headphones. Essential for my commute. Worth every cent.', 'Positive', '2026-03-18', 'Online', 'Electronics', 'Noise-Cancelling Headphones'),
    ('R-1019', '2TYPHX063nLHydF', 4, 'The Notebook has high quality paper. Only drawback is the cover scratches easily.', 'Positive', '2026-03-19', 'App', 'Office Supplies', 'Lined Notebook'),
    ('R-1020', '10ltT8M0ESCZD8M', 2, 'The Premium T-Shirt shrank significantly after the first wash, even following the care instructions.', 'Negative', '2026-03-20', 'Retail Store', 'Apparel', 'Premium T-Shirt');

-- load data into email sends tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_SENDS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_SEND_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email opens tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_OPENS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_OPEN_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email clicks tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_CLICKS"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, null, $28, $29, $30, $31
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_CLICK_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;

-- load data into email unsubscribes tables
COPY INTO "BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_UNSUBSCRIBES"
FROM (
    SELECT $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24
    FROM '@"BRAZE_ENGAGEMENT"."EMAIL_DATA"."EMAIL_STAGE"'
)
FILES = ('USERS_MESSAGES_EMAIL_UNSUBSCRIBE_VIEW.csv')
FILE_FORMAT = (
    TYPE=CSV,
    SKIP_HEADER=1,
    FIELD_DELIMITER=',',
    TRIM_SPACE=TRUE,
    FIELD_OPTIONALLY_ENCLOSED_BY='"',
    REPLACE_INVALID_CHARACTERS=TRUE,
    DATE_FORMAT=AUTO,
    TIME_FORMAT=AUTO,
    TIMESTAMP_FORMAT=AUTO
)
ON_ERROR=ABORT_STATEMENT;
```

### Verify Data Load

Run the following queries to verify that your data has been loaded successfully:

```sql
-- view changelog table data
SELECT * FROM BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS LIMIT 10;

-- view email sends data
SELECT * FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_SENDS LIMIT 10;

-- view email open data
SELECT * FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_OPENS LIMIT 10;

-- view email click data
SELECT * FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_CLICKS LIMIT 10;

-- view email unsubscribes data
SELECT * FROM BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_UNSUBSCRIBES LIMIT 10;

-- view product reviews data
SELECT * FROM BRAZE_ENGAGEMENT.EMAIL_DATA.PRODUCT_REVIEWS LIMIT 10;
```

## Create Semantic View

Now we'll create a Semantic View that enables natural language queries on our structured email engagement data using Cortex Analyst. Unlike a traditional semantic model YAML file, a Semantic View is a first-class database object that can be managed with SQL.

Run the following SQL to create the semantic view:

```sql
USE DATABASE BRAZE_ENGAGEMENT;
USE SCHEMA EMAIL_DATA;

CREATE OR REPLACE SEMANTIC VIEW CAMPAIGN_ANALYTICS_VIEW
  TABLES (
    sends AS BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_SENDS
      PRIMARY KEY (ID)
      COMMENT = 'Email send events from Braze campaigns',

    opens AS BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_OPENS
      PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
      COMMENT = 'Email open events from Braze campaigns',

    clicks AS BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_CLICKS
      PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
      COMMENT = 'Email click events from Braze campaigns',

    unsubs AS BRAZE_ENGAGEMENT.EMAIL_DATA.EMAIL_UNSUBSCRIBES
      PRIMARY KEY (DISPATCH_ID, EXTERNAL_USER_ID)
      COMMENT = 'Email unsubscribe events from Braze campaigns',

    campaigns AS BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_CHANGELOGS
      PRIMARY KEY (API_ID)
      COMMENT = 'Campaign metadata and changelog information'
  )

  RELATIONSHIPS (
    sends(CAMPAIGN_API_ID) REFERENCES campaigns(API_ID),
    opens(CAMPAIGN_API_ID) REFERENCES campaigns(API_ID),
    clicks(CAMPAIGN_API_ID) REFERENCES campaigns(API_ID),
    unsubs(CAMPAIGN_API_ID) REFERENCES campaigns(API_ID)
  )

  DIMENSIONS (
    sends.send_time AS sends.TIME
      COMMENT = 'Timestamp when the email was sent',
    sends.timezone AS sends.TIMEZONE
      COMMENT = 'Timezone of the recipient',
    sends.gender AS sends.GENDER
      COMMENT = 'Gender of the recipient',
    sends.external_user_id AS sends.EXTERNAL_USER_ID
      COMMENT = 'External user identifier',
    sends.dispatch_id AS sends.DISPATCH_ID
      COMMENT = 'Unique dispatch identifier',
    sends.campaign_api_id AS sends.CAMPAIGN_API_ID
      COMMENT = 'Campaign API identifier',
    sends.message_variation_api_id AS sends.MESSAGE_VARIATION_API_ID
      COMMENT = 'Message variation API identifier',

    opens.open_time AS opens.TIME
      COMMENT = 'Timestamp when the email was opened',
    opens.timezone AS opens.TIMEZONE
      COMMENT = 'Timezone of the recipient',
    opens.gender AS opens.GENDER
      COMMENT = 'Gender of the recipient',
    opens.external_user_id AS opens.EXTERNAL_USER_ID
      COMMENT = 'External user identifier',
    opens.dispatch_id AS opens.DISPATCH_ID
      COMMENT = 'Unique dispatch identifier',
    opens.campaign_api_id AS opens.CAMPAIGN_API_ID
      COMMENT = 'Campaign API identifier',

    clicks.click_time AS clicks.TIME
      COMMENT = 'Timestamp when the email link was clicked',
    clicks.timezone AS clicks.TIMEZONE
      COMMENT = 'Timezone of the recipient',
    clicks.gender AS clicks.GENDER
      COMMENT = 'Gender of the recipient',
    clicks.external_user_id AS clicks.EXTERNAL_USER_ID
      COMMENT = 'External user identifier',
    clicks.dispatch_id AS clicks.DISPATCH_ID
      COMMENT = 'Unique dispatch identifier',
    clicks.campaign_api_id AS clicks.CAMPAIGN_API_ID
      COMMENT = 'Campaign API identifier',
    clicks.url AS clicks.URL
      COMMENT = 'URL that was clicked',
    clicks.link_alias AS clicks.LINK_ALIAS
      COMMENT = 'Alias for the clicked link',

    unsubs.unsub_time AS unsubs.TIME
      COMMENT = 'Timestamp when user unsubscribed',
    unsubs.timezone AS unsubs.TIMEZONE
      COMMENT = 'Timezone of the recipient',
    unsubs.gender AS unsubs.GENDER
      COMMENT = 'Gender of the recipient',
    unsubs.external_user_id AS unsubs.EXTERNAL_USER_ID
      COMMENT = 'External user identifier',
    unsubs.dispatch_id AS unsubs.DISPATCH_ID
      COMMENT = 'Unique dispatch identifier',
    unsubs.campaign_api_id AS unsubs.CAMPAIGN_API_ID
      COMMENT = 'Campaign API identifier',

    campaigns.campaign_name AS campaigns.NAME
      COMMENT = 'Name of the campaign',
    campaigns.api_id AS campaigns.API_ID
      COMMENT = 'Unique API identifier for the campaign'
  )

  METRICS (
    sends.total_sends AS COUNT(sends.ID)
      COMMENT = 'Total number of emails sent',
    sends.unique_sends AS COUNT(DISTINCT sends.EXTERNAL_USER_ID)
      COMMENT = 'Number of unique users who received emails',

    opens.total_opens AS COUNT(opens.ID)
      COMMENT = 'Total number of email opens',
    opens.unique_openers AS COUNT(DISTINCT opens.EXTERNAL_USER_ID)
      COMMENT = 'Number of unique users who opened emails',

    clicks.total_clicks AS COUNT(clicks.ID)
      COMMENT = 'Total number of email clicks',
    clicks.unique_clickers AS COUNT(DISTINCT clicks.EXTERNAL_USER_ID)
      COMMENT = 'Number of unique users who clicked',

    unsubs.total_unsubs AS COUNT(unsubs.ID)
      COMMENT = 'Total number of unsubscribes',
    unsubs.unique_unsubs AS COUNT(DISTINCT unsubs.EXTERNAL_USER_ID)
      COMMENT = 'Number of unique users who unsubscribed'
  )

  COMMENT = 'Semantic view for Braze email engagement analytics including sends, opens, clicks, and unsubscribes'

  AI_SQL_GENERATION '
- "Engagement" is defined as opens or clicks
- "Success" is defined as opens or clicks
- This dataset contains email engagement data spanning from June 2023 through June 2025
- When suggesting time-based queries, use specific date ranges like "in 2024", "in 2025", "in June 2025", "in the first half of 2025", or "between January and June 2025"
- Avoid suggesting queries with "last month", "this month", or "recent" timeframes since the data has a fixed range ending in June 2025
- The most recent data available is from June 2025, so queries should reference that timeframe or earlier periods within the dataset range
- When users ask about recent performance, interpret this as referring to the most recent data available (June 2025 or late 2024/early 2025)
';

-- Verify the semantic view was created
SHOW SEMANTIC VIEWS IN SCHEMA BRAZE_ENGAGEMENT.EMAIL_DATA;
```

The semantic view defines:
- **5 logical tables** with primary keys and relationships
- **Dimensions** for time, timezone, gender, user IDs, and campaign information
- **8 metrics** for total and unique counts of sends, opens, clicks, and unsubscribes
- **AI instructions** to guide Cortex Analyst in generating accurate SQL

## Create Cortex Search Service

Now we'll create a Cortex Search Service to enable semantic search on our product reviews. This allows us to use RAG (Retrieval Augmented Generation) to analyze unstructured customer feedback.

```sql
USE DATABASE BRAZE_ENGAGEMENT;
USE SCHEMA EMAIL_DATA;

CREATE OR REPLACE CORTEX SEARCH SERVICE PRODUCT_REVIEWS_SEARCH
  ON REVIEW_TEXT
  ATTRIBUTES RATING, PRODUCT_SENTIMENT, PURCHASE_LOCATION, PRODUCT_CATEGORY, ITEM_NAME
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (
    SELECT
        REVIEW_ID,
        USER_ID,
        RATING,
        REVIEW_TEXT,
        PRODUCT_SENTIMENT,
        REVIEW_DATE,
        PURCHASE_LOCATION,
        PRODUCT_CATEGORY,
        ITEM_NAME
    FROM BRAZE_ENGAGEMENT.EMAIL_DATA.PRODUCT_REVIEWS
  );

-- Verify the search service was created
SHOW CORTEX SEARCH SERVICES IN SCHEMA BRAZE_ENGAGEMENT.EMAIL_DATA;
```

The Cortex Search Service:
- Indexes the `REVIEW_TEXT` column for semantic search
- Includes filterable attributes like rating, sentiment, location, category, and item name
- Automatically updates with a 1-hour target lag
- Enables natural language queries over unstructured review data

## Configure Snowflake Intelligence

Now we'll set up Snowflake Intelligence with an agent that combines both the Semantic View (for structured campaign data) and the Cortex Search Service (for unstructured product reviews).

### Access Snowflake Intelligence

1. In Snowsight, navigate to **AI & ML** > **Snowflake Intelligence**
2. Click **+ New Agent** to create a new agent

### Configure the Agent

Set up your agent with the following configuration:

**Agent Name:** Marketing Analytics Agent

**Description:** An AI assistant that helps marketers analyze email campaign performance and customer product reviews to optimize marketing strategies.

### Add Tools

Add the following tools to your agent:

**Tool 1: Semantic View (Structured Data)**
- Type: Cortex Analyst
- Semantic View: `BRAZE_ENGAGEMENT.EMAIL_DATA.CAMPAIGN_ANALYTICS_VIEW`
- Description: Query email campaign engagement data including sends, opens, clicks, and unsubscribes

**Tool 2: Cortex Search (Unstructured Data)**
- Type: Cortex Search
- Search Service: `BRAZE_ENGAGEMENT.EMAIL_DATA.PRODUCT_REVIEWS_SEARCH`
- Description: Search and analyze customer product reviews for sentiment and feedback insights

### Save and Activate

Click **Save** to create your agent. The agent is now ready to answer questions using both structured campaign data and unstructured product reviews.

## Using Snowflake Intelligence

Now let's explore how to use Snowflake Intelligence to gain marketing insights from both your structured and unstructured data.

### Sample Questions for Structured Data (Campaign Analytics)

Try these questions to analyze your email campaign performance:

**Basic Metrics:**
- "How many emails were sent in total?"
- "What is the overall open rate across all campaigns?"
- "Which campaign had the most clicks?"

**Time-based Analysis:**
- "Show me email engagement trends by month in 2024"
- "Which campaigns had the highest unsubscribe rates in the first half of 2025?"

**Segmentation:**
- "What timezone had the highest engagement for our campaigns?"
- "Break down opens and clicks by gender"

**Campaign Performance:**
- "What campaign had the most unsubscribes over all time?"
- "Compare engagement metrics across all campaigns"

### Sample Questions for Unstructured Data (Product Reviews)

Try these questions to analyze customer feedback:

**Sentiment Analysis:**
- "What are customers saying about electronics products?"
- "What are the main complaints in negative reviews?"
- "Summarize the positive feedback we're receiving"

**Product Insights:**
- "Which products have the best customer feedback?"
- "What issues are customers having with apparel?"
- "What do customers think about our home goods?"

**Channel Analysis:**
- "How do reviews differ between online and retail store purchases?"
- "What are app customers saying about their purchases?"

### Sample Questions Combining Both Data Sources

These questions demonstrate the power of combining structured and unstructured data:

**Strategic Planning:**
- "What should my email marketing optimization strategy be based on campaign performance and customer feedback?"
- "Based on product reviews and email engagement, which product categories should we focus our next campaign on?"
- "What improvements should we make to our marketing approach based on both campaign metrics and customer sentiment?"

**Customer Experience:**
- "How can we reduce unsubscribes based on what customers are saying in reviews?"
- "Which products with positive reviews should we highlight in our email campaigns?"
- "What messaging resonates with customers based on review feedback and click patterns?"

### Understanding the Output

When you ask questions, Snowflake Intelligence will:

1. **Determine the appropriate tool(s)** to use based on your question
2. **For structured data questions**: Generate and execute SQL queries against the semantic view
3. **For unstructured data questions**: Perform semantic search on product reviews and synthesize insights
4. **For combined questions**: Use both tools to provide comprehensive answers
5. **Provide actionable insights** tailored for marketing decision-making

## Conclusion And Resources

Congratulations! You've successfully built an intelligent marketing analytics solution that combines Braze email engagement data with product reviews using Snowflake's Cortex AI capabilities.

### What You Learned

You now have experience with:
- Setting up Snowflake environment for Braze engagement data and product reviews
- Creating Semantic Views for structured data analysis with SQL DDL
- Creating Cortex Search Services for unstructured data analysis (RAG)
- Using Snowflake Intelligence to query both structured and unstructured data
- Combining multiple AI tools for comprehensive marketing insights

### What You Built

Your complete solution includes:
- **Data Pipeline**: Stores and processes Braze email engagement data and product reviews in Snowflake
- **Semantic View**: Enables natural language queries on structured campaign data through Cortex Analyst
- **Cortex Search Service**: Enables semantic search on unstructured product reviews
- **Snowflake Intelligence Agent**: Combines both tools for comprehensive marketing analysis

### Key Capabilities

Your solution can:
- Query email campaign performance using natural language
- Search and analyze customer product reviews semantically
- Combine insights from both structured and unstructured data
- Provide actionable recommendations for marketing optimization
- Maintain data integrity by grounding responses in actual data

### Next Steps

To extend this solution, consider:
- Adding more Braze data tables (push notifications, in-app messages, etc.)
- Incorporating additional product review sources
- Creating scheduled data refreshes for real-time insights
- Building custom agents for specific marketing use cases
- Implementing user access controls and sharing capabilities

### Resources

- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex)
- [Semantic Views Documentation](https://docs.snowflake.com/en/user-guide/views-semantic/overview)
- [Cortex Search Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search)
- [Snowflake Intelligence Documentation](https://docs.snowflake.com/en/user-guide/snowflake-cortex/snowflake-intelligence)
- [Braze Data Export Documentation](https://www.braze.com/docs/user_guide/data_and_analytics/export_braze_data/)

You now have the foundation to build sophisticated, AI-powered analytics applications that can transform how marketing teams interact with their data!
