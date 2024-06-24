author: Charlie Hammond
id: tasty_bytes_rag_chatbot_using_cortex_and_streamlit
summary: This application supports Tasty Bytes management by analyzing both customer reviews and food truck inspections, streamlining communication with truck owners to improve the overall customer experience.
categories: Getting-Started, Tasty-Bytes, Cortex
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Getting Started, Snowflake Cortex, Streamlit

# Tasty Bytes - Enhance Customer Experience Streamlit App
<!-- ------------------------ -->
## Overview 
Duration: 1

![banner](assets/ece_header.png)

Welcome to the Powered by Tasty Bytes - Enhance Customer Experience Streamlit App Quickstart!

This application supports Tasty Bytes management by analyzing both customer reviews and food truck inspections, streamlining communication with truck owners to improve the overall customer experience. By leveraging Cortex functions, it conducts sentiment analysis to assist in drafting emails for owners. Moreover, it includes built-in analytics for users to interact with review data and generate plots using LLM's capabilities. Additionally, the integration of Document AI enhances its analytical prowess by extracting insights from handwritten, unstructured inspection documents.

### What You’ll Learn 
- How to build a Streamlit in Snowflake App
- 

### What You’ll Need 
- Snowflake account 

### What You’ll Build 
- A Cortex LLM chatbot using Streamlit in Snowflake

<!-- ------------------------ -->
## Setup
Duration: 10

### Create Snowflake Database, Schema and Warehouse

```sql
CREATE OR REPLACE DATABASE tasty_bytes_enhancing_customer_experience;

--Schema
CREATE OR REPLACE SCHEMA tasty_bytes_enhancing_customer_experience.raw_doc;

--Warehouse
CREATE OR REPLACE WAREHOUSE tasty_bytes_enhancing_customer_experience_wh with
WAREHOUSE_SIZE = LARGE
AUTO_SUSPEND = 60;
```

### Load App Data

```sql

CREATE OR REPLACE DATABASE tasty_bytes_enhancing_customer_experience;

--Schema
CREATE OR REPLACE SCHEMA tasty_bytes_enhancing_customer_experience.raw_doc;
CREATE OR REPLACE SCHEMA tasty_bytes_enhancing_customer_experience.raw_pos;
CREATE OR REPLACE SCHEMA tasty_bytes_enhancing_customer_experience.harmonized;
CREATE OR REPLACE SCHEMA tasty_bytes_enhancing_customer_experience.analytics;

--Warehouse
CREATE OR REPLACE WAREHOUSE tasty_bytes_enhancing_customer_experience_wh with
WAREHOUSE_SIZE = LARGE
AUTO_SUSPEND = 60;

CREATE OR REPLACE FILE FORMAT tasty_bytes_enhancing_customer_experience.raw_doc.csv_ff 
TYPE = 'csv';

CREATE OR REPLACE STAGE tasty_bytes_enhancing_customer_experience.raw_doc.csvload
COMMENT = 'Quickstarts S3 Stage Connection'
file_format = tasty_bytes_chatbot.app.csv_ff; 

CREATE OR REPLACE STAGE tasty_bytes_enhancing_customer_experience.raw_doc.inspection_reports
COMMENT = 'Inspection reports images';

-- raw layer
CREATE OR REPLACE TABLE tasty_bytes_enhancing_customer_experience.raw_doc.inspection_report_raw_extract (
	FILE_NAME VARCHAR(16777216),
	EXTRACTION_TIMESTAMP TIMESTAMP_LTZ(9),
	INSPECTION_REPORT_OBJECT VARIANT
);

CREATE OR REPLACE TABLE tasty_bytes_enhancing_customer_experience.raw_doc.inspection_report_ref (
	IRR_ID NUMBER(38,0),
	COLUMN_NAME VARCHAR(16777216),
	DESCRIPTION VARCHAR(16777216),
	CATEGORY VARCHAR(16777216)
);

CREATE OR REPLACE TABLE tasty_bytes_enhancing_customer_experience.raw_pos.truck (
	TRUCK_ID NUMBER(38,0),
	MENU_TYPE_ID NUMBER(38,0),
	PRIMARY_CITY VARCHAR(16777216),
	REGION VARCHAR(16777216),
	ISO_REGION VARCHAR(16777216),
	COUNTRY VARCHAR(16777216),
	ISO_COUNTRY_CODE VARCHAR(16777216),
	FRANCHISE_FLAG NUMBER(38,0),
	YEAR NUMBER(38,0),
	MAKE VARCHAR(16777216),
	MODEL VARCHAR(16777216),
	EV_FLAG NUMBER(38,0),
	FRANCHISE_ID NUMBER(38,0),
	TRUCK_OPENING_DATE DATE
);

CREATE OR REPLACE TABLE tasty_bytes_enhancing_customer_experience.raw_pos.menu (
	MENU_ID NUMBER(19,0),
	MENU_TYPE_ID NUMBER(38,0),
	MENU_TYPE VARCHAR(16777216),
	TRUCK_BRAND_NAME VARCHAR(16777216),
	MENU_ITEM_ID NUMBER(38,0),
	MENU_ITEM_NAME VARCHAR(16777216),
	ITEM_CATEGORY VARCHAR(16777216),
	ITEM_SUBCATEGORY VARCHAR(16777216),
	COST_OF_GOODS_USD NUMBER(38,4),
	SALE_PRICE_USD NUMBER(38,4),
	MENU_ITEM_HEALTH_METRICS_OBJ VARIANT
);

-- harmonized
CREATE OR REPLACE VIEW tasty_bytes_enhancing_customer_experience.harmonized.inspection_reports_v(
	DATE,
	TRUCK_ID,
	TRUCK_BRAND_NAME,
	CITY,
	COUNTRY,
	PIC_PRESENT,
	PIC_KNOWLEDGE,
	HANDS_CLEAN_WASHED,
	ADEQUATE_HW_FACILITIES,
	FOOD_APPROVED_SOURCE,
	FOOD_PROPER_TEMP,
	THERMOMETERS_ACCURATE,
	FOOD_PROTECTED,
	FOOD_SURFACE_CLEAN,
	NONFOOD_SURFACE_CLEAN,
	WATER_ICE_SOURCE_APPROVED,
	WATER_ICE_CONTAMINANT_FREE,
	UTENSILS_PROPER_STORAGE,
	GLOVES_USE_PROPER,
	WATER_PRESSURE_ADEQUATE,
	SEWAGE_DISPOSED_PROPERLY,
	GARBAGE_DISPOSED_PROPERLY,
	VENTILATION_LIGHTING_ADEQUATE,
	TIRES_ADEQUATE,
	VEHICLE_WELL_MAINTAINED,
	FILE_NAME,
	SCOPED_URL,
	PRESIGNED_URL
) AS (
WITH _menu_and_truck_name AS (SELECT DISTINCT menu_type_id, truck_brand_name FROM tasty_bytes_enhancing_customer_experience.raw_pos.menu)
SELECT 
    TO_DATE(REPLACE(inspection_report_object:"DATE"[0].value::varchar,'-','/')) AS date,
    inspection_report_object:"TRUCK_ID"[0].value::integer AS truck_id,
    mt.truck_brand_name,
    INITCAP(inspection_report_object:"CITY"[0].value::varchar) AS city,
    CASE 
        WHEN inspection_report_object:"COUNTRY"[0].value::varchar IN ('USA','US') THEN 'United States'
        ELSE inspection_report_object:"COUNTRY"[0].value::varchar
    END AS country,
    CASE 
        WHEN inspection_report_object:"PIC_PRESENT"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"PIC_PRESENT"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"PIC_PRESENT"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS pic_present,
    CASE
        WHEN inspection_report_object:"PIC_KNOWLEDGE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"PIC_KNOWLEDGE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"PIC_KNOWLEDGE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS pic_knowledge,
    CASE 
        WHEN inspection_report_object:"HANDS_CLEAN_WASHED"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"HANDS_CLEAN_WASHED"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"HANDS_CLEAN_WASHED"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS hands_clean_washed,
    CASE 
        WHEN inspection_report_object:"ADEQUATE_HW_FACILITIES"[0].value::varchar  = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"ADEQUATE_HW_FACILITIES"[0].value::varchar  = 'N' THEN 'Fail'
        WHEN inspection_report_object:"ADEQUATE_HW_FACILITIES"[0].value::varchar  = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS adequate_hw_facilities,
    CASE
        WHEN inspection_report_object:"FOOD_APPROVED_SOURCE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"FOOD_APPROVED_SOURCE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"FOOD_APPROVED_SOURCE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS food_approved_source,
    CASE
        WHEN inspection_report_object:"FOOD_PROPER_TEMP"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"FOOD_PROPER_TEMP"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"FOOD_PROPER_TEMP"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS food_proper_temp,
    CASE
        WHEN inspection_report_object:"THERMOMETERS_ACCURATE"[0].value::varchar  = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"THERMOMETERS_ACCURATE"[0].value::varchar  = 'N' THEN 'Fail'
        WHEN inspection_report_object:"THERMOMETERS_ACCURATE"[0].value::varchar  = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS thermometers_accurate,
    CASE
        WHEN inspection_report_object:"FOOD_PROTECTED"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"FOOD_PROTECTED"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"FOOD_PROTECTED"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS food_protected,
    CASE
        WHEN inspection_report_object:"FOOD_SURFACE_CLEAN"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"FOOD_SURFACE_CLEAN"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"FOOD_SURFACE_CLEAN"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS food_surface_clean,
    CASE
        WHEN inspection_report_object:"NONFOOD_SURFACE_CLEAN"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"NONFOOD_SURFACE_CLEAN"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"NONFOOD_SURFACE_CLEAN"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS nonfood_surface_clean,
    CASE
        WHEN inspection_report_object:"WATER_ICE_SOURCE_APPROVED"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"WATER_ICE_SOURCE_APPROVED"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"WATER_ICE_SOURCE_APPROVED"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS water_ice_source_approved,
    CASE
        WHEN inspection_report_object:"WATER_ICE_CONTAMINANT_FREE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"WATER_ICE_CONTAMINANT_FREE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"WATER_ICE_CONTAMINANT_FREE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed' 
    END AS water_ice_contaminant_free,
    CASE
        WHEN inspection_report_object:"UTENSILS_PROPER_STORAGE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"UTENSILS_PROPER_STORAGE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"UTENSILS_PROPER_STORAGE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed' 
    END AS utensils_proper_storage,
    CASE
        WHEN inspection_report_object:"GLOVES_USE_PROPER"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"GLOVES_USE_PROPER"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"GLOVES_USE_PROPER"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed' 
    END AS gloves_use_proper,
    CASE
        WHEN inspection_report_object:"WATER_PRESSURE_ADEQUATE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"WATER_PRESSURE_ADEQUATE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"WATER_PRESSURE_ADEQUATE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed' 
    END AS water_pressure_adequate,
    CASE
        WHEN inspection_report_object:"SEWAGE_DISPOSED_PROPERLY"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"SEWAGE_DISPOSED_PROPERLY"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"SEWAGE_DISPOSED_PROPERLY"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed' 
    END AS sewage_disposed_properly,
    CASE
        WHEN inspection_report_object:"GARBAGE_DISPOSED_PROPERLY"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"GARBAGE_DISPOSED_PROPERLY"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"GARBAGE_DISPOSED_PROPERLY"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS garbage_disposed_properly,
    CASE
        WHEN inspection_report_object:"VENTILATION_LIGHTING_ADEQUATE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"VENTILATION_LIGHTING_ADEQUATE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"VENTILATION_LIGHTING_ADEQUATE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS ventilation_lighting_adequate,
    CASE
        WHEN inspection_report_object:"TIRES_ADEQUATE"[0].value::varchar = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"TIRES_ADEQUATE"[0].value::varchar = 'N' THEN 'Fail'
        WHEN inspection_report_object:"TIRES_ADEQUATE"[0].value::varchar = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS tires_adequate,
    CASE
        WHEN inspection_report_object:"VEHICLE_WELL_MAINTAINED"[0].value::varchar  = 'Y' THEN 'Pass'
        WHEN inspection_report_object:"VEHICLE_WELL_MAINTAINED"[0].value::varchar  = 'N' THEN 'Fail'
        WHEN inspection_report_object:"VEHICLE_WELL_MAINTAINED"[0].value::varchar  = 'X' THEN 'Not Observed'
        ELSE 'Not Observed'
    END AS vehicle_well_maintained,
    file_name,
    BUILD_SCOPED_FILE_URL(@tasty_bytes_enhancing_customer_experience.raw_doc.inspection_reports, file_name) AS scoped_url,
    GET_PRESIGNED_URL(@tasty_bytes_enhancing_customer_experience.raw_doc.inspection_reports, file_name) AS presigned_url
FROM tasty_bytes_enhancing_customer_experience.raw_doc.inspection_report_raw_extract ir
JOIN tasty_bytes_enhancing_customer_experience.raw_pos.truck t
    ON ir.inspection_report_object:"TRUCK_ID"[0].value::integer = t.truck_id
JOIN _menu_and_truck_name mt
    ON t.menu_type_id = mt.menu_type_id
  );

CREATE OR REPLACE VIEW tasty_bytes_enhancing_customer_experience.harmonized.inspection_report_ref_v(
	IRR_ID,
	COLUMN_NAME,
	DESCRIPTION,
	CATEGORY
) as (
SELECT * FROM tasty_bytes_enhancing_customer_experience.raw_doc.inspection_report_ref
  );

-- analytics
CREATE OR REPLACE VIEW tasty_bytes_enhancing_customer_experience.analytics.inspection_reports_v(
	DATE,
	TRUCK_ID,
	TRUCK_BRAND_NAME,
	CITY,
	COUNTRY,
	PIC_PRESENT,
	PIC_KNOWLEDGE,
	HANDS_CLEAN_WASHED,
	ADEQUATE_HW_FACILITIES,
	FOOD_APPROVED_SOURCE,
	FOOD_PROPER_TEMP,
	THERMOMETERS_ACCURATE,
	FOOD_PROTECTED,
	FOOD_SURFACE_CLEAN,
	NONFOOD_SURFACE_CLEAN,
	WATER_ICE_SOURCE_APPROVED,
	WATER_ICE_CONTAMINANT_FREE,
	UTENSILS_PROPER_STORAGE,
	GLOVES_USE_PROPER,
	WATER_PRESSURE_ADEQUATE,
	SEWAGE_DISPOSED_PROPERLY,
	GARBAGE_DISPOSED_PROPERLY,
	VENTILATION_LIGHTING_ADEQUATE,
	TIRES_ADEQUATE,
	VEHICLE_WELL_MAINTAINED,
	FILE_NAME,
	SCOPED_URL,
	PRESIGNED_URL,
	OVERALL_RESULT
) as (
    
        
SELECT *,
   CASE
       WHEN (
             CASE WHEN pic_present = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN pic_knowledge = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN hands_clean_washed = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN adequate_hw_facilities = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN food_approved_source = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN food_proper_temp = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN thermometers_accurate = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN food_protected = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN food_surface_clean = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN nonfood_surface_clean = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN water_ice_source_approved = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN water_ice_contaminant_free = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN utensils_proper_storage = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN gloves_use_proper = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN water_pressure_adequate = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN sewage_disposed_properly = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN garbage_disposed_properly = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN ventilation_lighting_adequate = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN tires_adequate = 'Fail' THEN 1 ELSE 0 END +
             CASE WHEN vehicle_well_maintained = 'Fail' THEN 1 ELSE 0 END) >= 5 THEN 'Fail'
       ELSE 'Pass'
       END AS overall_result
FROM tasty_bytes_enhancing_customer_experience.harmonized.inspection_reports_v
  );

CREATE OR REPLACE TABLE tasty_bytes_enhancing_customer_experience.analytics.review_analysis_output (
	TRUCK_ID NUMBER(38,0),
	REVIEW_ID NUMBER(18,0),
	REVIEW VARCHAR(16777216),
	SENTIMENT FLOAT,
	TRANSLATED_REVIEW VARCHAR(16777216),
	RATING VARCHAR(16777216),
	CLEAN_RATING VARCHAR(16777216),
	RECOMMEND VARCHAR(16777216),
	CLEAN_RECOMMEND VARCHAR(16777216),
	CATEGORY_SENTIMENT VARCHAR(16777216)
);

CREATE OR REPLACE VIEW tasty_bytes_enhancing_customer_experience.analytics.inspection_reports_unpivot_v(
	DATE,
	TRUCK_ID,
	CATEGORY,
	INSPECTION_ITEM,
	DESCRIPTION,
	RESULT
) as (
WITH _unpivot_inspections AS (
    SELECT 
        date, 
        truck_id,
        inspection_item,
        result
    FROM 
        (SELECT 
            date, 
            truck_id,
            pic_present, 
            pic_knowledge, 
            hands_clean_washed, 
            adequate_hw_facilities, 
            food_approved_source, 
            food_proper_temp, 
            thermometers_accurate, 
            food_protected, 
            food_surface_clean, 
            nonfood_surface_clean, 
            water_ice_source_approved, 
            water_ice_contaminant_free, 
            utensils_proper_storage, 
            gloves_use_proper, 
            water_pressure_adequate, 
            sewage_disposed_properly, 
            garbage_disposed_properly, 
            ventilation_lighting_adequate, 
            tires_adequate, 
            vehicle_well_maintained
        FROM tasty_bytes_enhancing_customer_experience.harmonized.inspection_reports_v
        ) UNPIVOT (
            result FOR inspection_item IN (
                pic_present, 
                pic_knowledge, 
                hands_clean_washed, 
                adequate_hw_facilities, 
                food_approved_source, 
                food_proper_temp, 
                thermometers_accurate, 
                food_protected, 
                food_surface_clean, 
                nonfood_surface_clean, 
                water_ice_source_approved, 
                water_ice_contaminant_free, 
                utensils_proper_storage, 
                gloves_use_proper, 
                water_pressure_adequate, 
                sewage_disposed_properly, 
                garbage_disposed_properly, 
                ventilation_lighting_adequate, 
                tires_adequate, 
                vehicle_well_maintained
            )
        )
)
SELECT 
    u.date,
    u.truck_id,
    r.category,
    u.inspection_item,
    r.description,
    u.result
FROM _unpivot_inspections u
JOIN  tasty_bytes_enhancing_customer_experience.harmonized.inspection_report_ref_v r
    ON u.inspection_item = r.column_name
ORDER BY u.date, u.truck_id, u.inspection_item
  );

CREATE OR REPLACE VIEW tasty_bytes_enhancing_customer_experience.analytics.review_analysis_output_v(
	TRUCK_ID,
	REVIEW_ID,
	REVIEW,
	SENTIMENT,
	TRANSLATED_REVIEW,
	RATING,
	CLEAN_RATING,
	RECOMMEND,
	CLEAN_RECOMMEND,
	CATEGORY,
	CATEGORY_SENTIMENT,
	DETAILS
) AS (
SELECT 
    rao.* EXCLUDE category_sentiment,
    value:category::STRING as category,
    value:sentiment::STRING as category_sentiment,
    value:details::STRING as details
FROM tasty_bytes_enhancing_customer_experience.analytics.review_analysis_output rao,
LATERAL FLATTEN (PARSE_JSON(TO_VARIANT(rao.category_sentiment))) cs
  );

-- insert data
COPY INTO tasty_bytes_enhancing_customer_experience.raw_doc.inspection_report_raw_extract
FROM @tasty_bytes_enhancing_customer_experience.raw_doc.csvload/raw_doc/inspection_report_raw_extract/;

COPY INTO tasty_bytes_enhancing_customer_experience.raw_doc.inspection_report_ref
FROM @tasty_bytes_enhancing_customer_experience.raw_doc.csvload/raw_doc/inspection_report_ref/;

COPY INTO tasty_bytes_enhancing_customer_experience.raw_pos.truck
FROM @tasty_bytes_enhancing_customer_experience.raw_doc.csvload/raw_pos/truck/;

COPY INTO tasty_bytes_enhancing_customer_experience.raw_pos.menu
FROM @tasty_bytes_enhancing_customer_experience.raw_doc.csvload/raw_pos/menu/;

COPY INTO tasty_bytes_enhancing_customer_experience.analytics.review_analysis_output
FROM @tasty_bytes_enhancing_customer_experience.raw_doc.csvload/analytics/review_analysis_output/;

```

### Upload Streamlit Files

### Create Streamlit App

<!-- ------------------------ -->
## Creating a Step
Duration: 2

A single sfguide consists of multiple steps. These steps are defined in Markdown using Header 2 tag `##`. 

```markdown
## Step 1 Title
Duration: 3

All the content for the step goes here.

## Step 2 Title
Duration: 1

All the content for the step goes here.
```

To indicate how long each step will take, set the `Duration` under the step title (i.e. `##`) to an integer. The integers refer to minutes. If you set `Duration: 4` then a particular step will take 4 minutes to complete. 

The total sfguide completion time is calculated automatically for you and will be displayed on the landing page. 

<!-- ------------------------ -->
## Code Snippets, Info Boxes, and Tables
Duration: 2

Look at the [markdown source for this sfguide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate code snippets, info boxes, and download buttons. 

### JavaScript
```javascript
{ 
  key1: "string", 
  key2: integer,
  key3: "string"
}
```

### Java
```java
for (statement 1; statement 2; statement 3) {
  // code block to be executed
}
```

### Info Boxes
> aside positive
> 
>  This will appear in a positive info box.


> aside negative
> 
>  This will appear in a negative info box.

### Buttons
<button>

  [This is a download button](link.com)
</button>

### Tables
<table>
    <thead>
        <tr>
            <th colspan="2"> **The table header** </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>The table body</td>
            <td>with two columns</td>
        </tr>
    </tbody>
</table>

### Hyperlinking
[Youtube - Halsey Playlists](https://www.youtube.com/user/iamhalsey/playlists)

<!-- ------------------------ -->
## Images, Videos, and Surveys, and iFrames
Duration: 2

Look at the [markdown source for this guide](https://raw.githubusercontent.com/Snowflake-Labs/sfguides/master/site/sfguides/sample.md) to see how to use markdown to generate these elements. 

### Images
![Puppy](assets/SAMPLE.jpg)

### Videos
Videos from youtube can be directly embedded:
<video id="KmeiFXrZucE"></video>

### Inline Surveys
<form>
  <name>How do you rate yourself as a user of Snowflake?</name>
  <input type="radio" value="Beginner">
  <input type="radio" value="Intermediate">
  <input type="radio" value="Advanced">
</form>

### Embed an iframe
![https://codepen.io/MarioD/embed/Prgeja](https://en.wikipedia.org/wiki/File:Example.jpg "Try Me Publisher")

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 1

At the end of your Snowflake Guide, always have a clear call to action (CTA). This CTA could be a link to the docs pages, links to videos on youtube, a GitHub repo link, etc. 

If you want to learn more about Snowflake Guide formatting, checkout the official documentation here: [Formatting Guide](https://github.com/googlecodelabs/tools/blob/master/FORMAT-GUIDE.md)

### What You Learned
- creating steps and setting duration
- adding code snippets
- embedding images, videos, and surveys
- importing other markdown files

### Related Resources
- <link to github code repo>
- <link to documentation>
