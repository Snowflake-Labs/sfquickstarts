CREATE SCHEMA IF NOT EXISTS agriculture;

-- Read the whole JSON file into a psql variable, then into a temporary table
\set content `cat california_wine_country_visits_202409021224.json`
CREATE TEMP TABLE wine_json (doc jsonb);
INSERT INTO wine_json VALUES (:'content');

DROP TABLE IF EXISTS agriculture.california_wine_country_visits;
CREATE TABLE agriculture.california_wine_country_visits AS
SELECT
  (r->>'id')::integer                        AS id,
  r->>'winery or vineyard'                   AS winery_or_vineyard,
  r->>'ca wine region'                       AS ca_wine_region,
  r->>'ava appellation sub appellation'      AS ava_appellation_sub_appellation,
  r->>'website'                              AS website,
  r->>'price range'                          AS price_range,
  r->>'tasting room hours'                   AS tasting_room_hours,
  r->>'reservation required'                 AS reservation_required,
  r->>'winery description'                   AS winery_description,
  r->>'primary varietals'                    AS primary_varietals,
  r->>'tasting room experience'              AS tasting_room_experience,
  r->>'amenities'                            AS amenities,
  r->>'awards and accolades'                 AS awards_and_accolades,
  r->>'distance and travel time'             AS distance_and_travel_time,
  r->>'user rating'                          AS user_rating,
  r->>'secondary varietals'                  AS secondary_varietals,
  r->>'wine styles'                          AS wine_styles,
  r->>'events and activities'                AS events_and_activities,
  r->>'sustainability practices'             AS sustainability_practices,
  r->>'social media'                         AS social_media,
  r->>'address'                              AS address,
  r->>'city'                                 AS city,
  r->>'state'                                AS state,
  r->>'zip'                                  AS zip,
  r->>'phone'                                AS phone,
  r->>'winemaker'                            AS winemaker,
  r->>'kelly kohlleffel recommended'         AS kelly_kohlleffel_recommended
FROM wine_json, jsonb_array_elements(doc) AS r;

ALTER TABLE agriculture.california_wine_country_visits ADD PRIMARY KEY (id);
SELECT count(*) FROM agriculture.california_wine_country_visits;
