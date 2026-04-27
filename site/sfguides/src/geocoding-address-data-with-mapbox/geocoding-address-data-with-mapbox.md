author: chriswhong
id: geocoding-address-data-with-mapbox
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/applications-and-collaboration, snowflake-site:taxonomy/snowflake-feature/build
language: en
summary: Convert addresses to coordinates with Mapbox geocoding on Snowflake for location enrichment, mapping, and spatial analytics.
environments: 
status: Published
feedback link: https://github.com/chriswhong/sfquickstarts

# Geocoding Address Data with Mapbox

<!-- ------------------------ -->

## Overview

This Quickstart will help you get started with the __Mapbox Snowflake Native App__, which adds new stored procedures for geocoding, navigation, and Mapbox boundaries APIs and data that you can use in your SQL queries.  Geocoding converts your address data (e.g. "1600 Pennsylvania Ave, Washington, DC, 20500") into geographic coordinates which can be used for mapping and spatial analysis. Navigation stored procedures help calculate distance and duration between start and destination points, and calculate isochrones. Mapbox boundaries stored procedures allow you to do point-in-polygon lookups against the Mapbox boundaries dataset.

Mapbox geocoding, navigation, and boundaries APIs and data are used by companies for a variety of purposes, including asset tracking, supply chain and retail strategy, and analysis of demographic trends, elections, and real estate.

The Mapbox Snowflake Native App is powered by [Mapbox APIs](https://docs.mapbox.com/api) and the boundaries lookup is powered by [Mapbox Boundaries](https://www.mapbox.com/boundaries).

![logos](assets/logos.png)


### Prerequisites

- Familiarity with SQL and Snowflake
- Basic understanding of spatial concepts and geocoding (turning addresses into latitude and longitude coordinates)

### What You’ll Learn

- How to use the Mapbox app's functions to perform bulk geocoding on a snowflake table.
- How to export your new spatial data for use in third-party tools

### What You’ll Need

- Access to the snowflake GUI.
- The Mapbox Snowflake Native App installed in your snowflake environment.

### What You’ll Build

- SQL queries to geocode address data from a single column
- SQL queries to geocode address data from multiple columns (structured data)
- SQL queries to export geojson data from a table with latitude and longitude data
- SQL queries to reverse geocode coordinates and perform boundary lookups


© 2023 Mapbox, Inc

## Installing the Mapbox App

### Step 1

After you install the Mapbox application, go to "Data products", then click on "Apps", then click on the Mapbox app. Then from the Mapbox app, click on the "SETUP" link in the upper-left side of the screen and follow the steps. These steps will help create an API Integration and external functions required for the application to work.

Once you complete the steps using the "SETUP" link, return here to finish the rest of the installation steps.

### Step 2

You will need to do this step any time you want the Mapbox application to be able to access certain databases, schemas, and tables within your Snowflake account, specifying the names of those specific resources in your Snowflake account. The below is an example.

Grant access to allow the application to access databases, schemas, and tables within your Snowflake account. The below assumes you have a database called "mydatabase" with a schema called "testing", and a table called "sample_addresses". Also, if you did not name the application exactly "mapbox", change "mapbox" to the exact name of the Mapbox application.

```
GRANT USAGE ON DATABASE mydatabase to application mapbox;
GRANT USAGE ON SCHEMA mydatabase.testing to application mapbox;
GRANT SELECT ON TABLE mydatabase.testing.sample_addresses to application mapbox;
GRANT UPDATE ON TABLE mydatabase.testing.sample_addresses to application mapbox;
```

Note that some of the examples in the "Usage" section below use sample data from sample tables provided by the application. The application does not need additional privileges to run against those sample tables and data provided by the application.

## Usage

A general usage note: stored procedures must pass all parameters in the stored procedure signature. Pass "null" if you do not wish to use a given parameter. All of the examples act on sample data that comes with the application. Wherever you see "mapbox" as a parameter in the stored procedure examples, if you did not name the native app "mapbox" you must change "mapbox" to match whatever you named the app.

## Geocoding

The geocoding stored procedures comply with the [Mapbox Geocoding V6 API.](https://docs.mapbox.com/api/search/geocoding-v6/)

#### geocode_forward

Perform a forward geocode. [Refer to API documentation here.](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)

##### Procedure signature

```
CALL geocode_forward_enrich (
  DB_NAME VARCHAR,
  SCHEMA_NAME VARCHAR,
  TABLE_NAME VARCHAR,
  DESTINATION_COLUMN_NAME VARCHAR,
  INCREMENTAL BOOLEAN,
  QUERY VARCHAR,
  PARAM_BBOX VARCHAR,
  PARAM_COUNTRY VARCHAR,
  PARAM_FORMAT VARCHAR,
  PARAM_LANGUAGE VARCHAR,
  PARAM_PROXIMITY VARCHAR,
  PARAM_TYPES VARCHAR,
  PARAM_WORLDVIEW VARCHAR
)
```

All parameters must be passed to the stored procedure, but if you do not wish to use any particular parameters, pass null for that parameter. For all parameters that start with "PARAM" you may pass in a string literal value instead of referencing a table column name by surrounding it in three single-quotes, like '''myvalue'''.

- DB_NAME - the name of the database on which the stored procedure will act. Be sure you've given the application permissions to act on this database
- SCHEMA_NAME - the name of the schema on the database from the above parameter on which the stored procedure will act. Be sure you've given the application permissions to act on this schema
- TABLE_NAME - the name of the table on the database and schema from the above parameters on which the stored procedure will act. Be sure you've given the application permissions to act on this table
- DESTINATION_COLUMN_NAME - the name of the column in the above table to which the stored procedure will write the Mapbox value or response
- INCREMENTAL - if true, the stored procedure will not overwrite rows with a non-null value in the provided DESTINATION_COLUMN_NAME column.
- QUERY - column name in the above table to use as the query when forward geocoding
- PARAM_BBOX - column name in the above table to use as bbox filter [See the Mapbox API documentation for bounding box](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_COUNTRY - column name in the above table to use as country filter [See the Mapbox API documentation for country](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_FORMAT VARCHAR - column name in the above table to use as format [See the Mapbox API documentation for format](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_LANGUAGE VARCHAR - column name in the above table to use as language [See the Mapbox API documentation for language](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_PROXIMITY VARCHAR - column name in the above table to use as proximity [See the Mapbox API documentation for proximity](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_TYPES VARCHAR - column name in the above table to use as types filter [See the Mapbox API documentation for types](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_WORLDVIEW VARCHAR - column name in the above table to use as worldview [See the Mapbox API documentation for worldview](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)

##### Differences from normal Mapbox API

The following parameters mentioned in the Mapbox Geocoding V6 API documentation cannot be changed:

- `permanent` (defaults to true and cannot be changed)
- `limit` (defaults to 1 and cannot be changed)
- `autocomplete` (defaults to false and cannot be changed)

##### Examples

```
CALL mapbox.core.geocode_forward_enrich (
  'mapbox',
  'sample_data',
  'geocode_forward',
  'response',
  false,
  'query',
  null,
  null,
  null,
  null,
  null,
  null,
  null
);
```

This will update the mapbox.sample_data.geocode_forward table's "response" column and populate it with the forward geocoding result for each row

#### geocode_reverse

Perform a reverse geocode using the Mapbox Geocoding V6 endpoint. [Refer to API documentation here.](https://docs.mapbox.com/api/search/geocoding-v6/#reverse-geocoding)

##### Procedure signature

```
CALL mapbox.core.geocode_reverse_enrich (
  DB_NAME VARCHAR,
  SCHEMA_NAME VARCHAR,
  TABLE_NAME VARCHAR,
  DESTINATION_COLUMN_NAME VARCHAR,
  INCREMENTAL BOOLEAN,
  LONGITUDE VARCHAR,
  LATITUDE VARCHAR,
  PARAM_COUNTRY VARCHAR,
  PARAM_LANGUAGE VARCHAR,
  PARAM_TYPES VARCHAR,
  PARAM_WORLDVIEW VARCHAR
);
```

All parameters must be passed to the stored procedure, but if you do not wish to use any particular parameters, pass null for that parameter. For all parameters that start with "PARAM" you may pass in a string literal value instead of referencing a table column name by surrounding it in three single-quotes, like '''myvalue'''.

- DB_NAME - the name of the database on which the stored procedure will act. Be sure you've given the application permissions to act on this database
- SCHEMA_NAME - the name of the schema on the database from the above parameter on which the stored procedure will act. Be sure you've given the application permissions to act on this schema
- TABLE_NAME - the name of the table on the database and schema from the above parameters on which the stored procedure will act. Be sure you've given the application permissions to act on this table
- DESTINATION_COLUMN_NAME - the name of the column in the above table to which the stored procedure will write the Mapbox value or response
- INCREMENTAL - if true, the stored procedure will not overwrite rows with a non-null value in the provided DESTINATION_COLUMN_NAME column.
- LONGITUDE - column name in the above table to use as the longitude value when reverse geocoding
- LATITUDE - column name in the above table to use as the latitude value when reverse geocoding
- PARAM_COUNTRY - column name in the above table to use as country filter [See the Mapbox API documentation for country](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_LANGUAGE VARCHAR - column name in the above table to use as language [See the Mapbox API documentation for language](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_TYPES VARCHAR - column name in the above table to use as types filter [See the Mapbox API documentation for types](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)
- PARAM_WORLDVIEW VARCHAR - [See the Mapbox API documentation for worldview](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding)

##### Differences from normal Mapbox API

The following parameters mentioned in the Mapbox Geocoding V6 API documentation cannot be changed:

- `permanent` (defaults to true and cannot be changed)
- `limit` (defaults to 1 and cannot be changed)

##### Examples

```
CALL mapbox.core.geocode_reverse_enrich (
  'mapbox',
  'sample_data',
  'geocode_reverse',
  'response',
  false,
  'longitude',
  'latitude',
  null,
  null,
  null,
  null
);
```

This will update the mapbox.sample_data.geocode_reverse table's "response" column and populate it with the reverse geocoding result for each row

#### geocode_structured

Perform a structured forward geocode using the Mapbox Geocoding V6 endpoint. [Refer to API documentation here.](https://docs.mapbox.com/api/search/geocoding-v6/#structured-input)

##### Procedure signature

```
CALL mapbox.core.geocode_structured_enrich (
  DB_NAME VARCHAR,
  SCHEMA_NAME VARCHAR,
  TABLE_NAME VARCHAR,
  DESTINATION_COLUMN_NAME VARCHAR,
  INCREMENTAL BOOLEAN,
  ADDRESS_LINE1 VARCHAR,
  ADDRESS_NUMBER VARCHAR,
  STREET VARCHAR,
  BLOCK VARCHAR,
  PLACE VARCHAR,
  REGION VARCHAR,
  POSTCODE VARCHAR,
  LOCALITY VARCHAR,
  NEIGHBORHOOD VARCHAR,
  COUNTRY VARCHAR
);
```

All parameters must be passed to the stored procedure, but if you do not wish to use any particular parameters, pass null for that parameter. For all parameters that start with "PARAM" you may pass in a string literal value instead of referencing a table column name by surrounding it in three single-quotes, like '''myvalue'''.

- DB_NAME - the name of the database on which the stored procedure will act. Be sure you've given the application permissions to act on this database
- SCHEMA_NAME - the name of the schema on the database from the above parameter on which the stored procedure will act. Be sure you've given the application permissions to act on this schema
- TABLE_NAME - the name of the table on the database and schema from the above parameters on which the stored procedure will act. Be sure you've given the application permissions to act on this table
- DESTINATION_COLUMN_NAME - the name of the column in the above table to which the stored procedure will write the Mapbox value or response
- INCREMENTAL - if true, the stored procedure will not overwrite rows with a non-null value in the provided DESTINATION_COLUMN_NAME column.
- ADDRESS_LINE1 - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- ADDRESS_NUMBER - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- STREET - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- BLOCK - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- PLACE - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- REGION - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- POSTCODE - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- LOCALITY - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- NEIGHBORHOOD - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)
- COUNTRY - [See the Mapbox API documentation](https://docs.mapbox.com/api/search/geocoding-v6/#forward-geocoding-with-structured-input)

##### Differences from normal Mapbox API

None

##### Examples

```
CALL mapbox.core.geocode_structured_enrich (
  'mapbox',
  'sample_data',
  'geocode_structured',
  'response',
  false,
  null,
  'address_number',
  'address_street',
  null,
  'address_place',
  'address_region',
  null,
  null,
  null,
  null
);
```

This will update the mapbox.sample_data.geocode_structured table's "response" column and populate it with the structured geocoding result for each row

## Navigation

#### Distance and duration

The `distance_and_duration_enrich` procedure provides simplified access to the [Mapbox Matrix API](https://docs.mapbox.com/api/navigation/matrix/) with the primary difference being it can only calculate the distance and duration between two points. The result is an `OBJECT` value with structured contents that match the JSON responses provided by the Mapbox Matrix API.

##### Procedure signature

```
CALL mapbox.core.distance_and_duration_enrich(
  DB_NAME VARCHAR,
  SCHEMA_NAME VARCHAR,
  TABLE_NAME VARCHAR,
  DESTINATION_COLUMN_NAME VARCHAR,
  INCREMENTAL BOOLEAN,
  START_LONGITUDE VARCHAR,
  START_LATITUDE VARCHAR,
  END_LONGITUDE VARCHAR,
  END_LATITUDE VARCHAR,
  PROFILE VARCHAR
);
```

All parameters must be passed to the stored procedure, but if you do not wish to use any particular parameters, pass null for that parameter.

- DB_NAME - the name of the database on which the stored procedure will act. Be sure you've given the application permissions to act on this database
- SCHEMA_NAME - the name of the schema on the database from the above parameter on which the stored procedure will act. Be sure you've given the application permissions to act on this schema
- TABLE_NAME - the name of the table on the database and schema from the above parameters on which the stored procedure will act. Be sure you've given the application permissions to act on this table
- DESTINATION_COLUMN_NAME - the name of the column in the above table to which the stored procedure will write the Mapbox value or response
- INCREMENTAL - if true, the stored procedure will not overwrite rows with a non-null value in the provided DESTINATION_COLUMN_NAME column.
- START_LONGITUDE - the starting point longitude coordinate
- START_LATITUDE - the starting point latitiude coordinate
- END_LONGITUDE - the ending point longitude coodidnate
- END_LATITUDE - the ending point latitude coordinate
- PROFILE - See [Mapbox Matrix API documentation](https://docs.mapbox.com/api/navigation/matrix/). Must be one of 'mapbox/driving', 'mapbox/walking', 'mapbox/cycling', 'mapbox/driving-traffic'


##### Differences from the normal Mapbox API

- Only one source and one destination coordinate may be provided
- The `annotations` parameter cannot be changed, and is set to both distance and duration
- The `fallback_speed` parameter is not supported
- The `depart_at` parameter is not supported
- The `approaches` parameter is set to "unrestricted" and cannot be changed

##### Examples

Get distance and duration for two points:

```
CALL mapbox.core.distance_and_duration_enrich (
  'mapbox',
  'sample_data',
  'distance_and_duration',
  'response',
  false,
  'start_longitude',
  'start_latitude',
  'end_longitude',
  'end_latitude',
  'mapbox/walking'
);
```

#### Isochrone

The `isochrone_enrich` procedure provides a simplified interface to the [Mapbox Isochrone API](https://docs.mapbox.com/api/navigation/isochrone/). The result is a polygon `GEOGRAPHY` value.

##### Procedure signature

```
CALL mapbox.core.isochrone_enrich(
  DB_NAME VARCHAR,
  SCHEMA_NAME VARCHAR,
  TABLE_NAME VARCHAR,
  DESTINATION_COLUMN_NAME VARCHAR,
  INCREMENTAL BOOLEAN,
  LONGITUDE VARCHAR,
  LATITUDE VARCHAR,
  PROFILE VARCHAR,
  DISTANCE VARCHAR,
  METRIC VARCHAR
);
```

The value of `metric` must be either 'minutes' or 'meters'.

All parameters must be passed to the stored procedure, but if you do not wish to use any particular parameters, pass null for that parameter.

- DB_NAME - the name of the database on which the stored procedure will act. Be sure you've given the application permissions to act on this database
- SCHEMA_NAME - the name of the schema on the database from the above parameter on which the stored procedure will act. Be sure you've given the application permissions to act on this schema
- TABLE_NAME - the name of the table on the database and schema from the above parameters on which the stored procedure will act. Be sure you've given the application permissions to act on this table
- DESTINATION_COLUMN_NAME - the name of the column in the above table to which the stored procedure will write the Mapbox value or response
- INCREMENTAL - if true, the stored procedure will not overwrite rows with a non-null value in the provided DESTINATION_COLUMN_NAME column.
- LONGITUDE - the longitude coordinate around which to center the isochrone
- LATITUDE - the latitude coordinate around which to center the isochrone
- PROFILE - See [Mapbox Isochrone API documentation](https://docs.mapbox.com/api/navigation/isochrone/). Must be one of 'mapbox/driving', 'mapbox/walking', 'mapbox/cycling', 'mapbox/driving-traffic'
- DISTANCE - See [Mapbox Isochrone API documentation](https://docs.mapbox.com/api/navigation/isochrone/). Represents a value for 'metric'. If '10', and 'metric' is set to minutes, it signifies 10 minutes. If 'metric' is set to 'meters', it signifies 10 meters.
- METRIC - See [Mapbox Directions API documentation](https://docs.mapbox.com/api/navigation/directions/). Must be one of 'minutes' or 'meters'


##### Differences from the normal Mapbox API

Unlike the Mapbox API, the `isochrone` procedure will provide only one contour at a time.

The following parameters mentioned in the Mapbox Isochrone API documentation cannot be changed:

- `polygons` (defaults to `true`)
- all other _optional_ parameters are unset


##### Examples


```
CALL mapbox.core.isochrone_enrich (
  'mapbox',
  'sample_data',
  'isochrone',
  'response',
  false,
  'longitude',
  'latitude',
  'mapbox/walking',
  15,
  'minutes'
)
```

## Boundaries

#### mapbox_boundaries_reverse_enrich

Perform a point-in-polygon lookup on [Mapbox boundaries](https://www.mapbox.com/boundaries) data. This stored procedure is designed to be given a database, schema, and table on which to operate, and will fill in a specified column in that table with the specified boundaries layer.

##### Stored procedure signature

```
CALL mapbox.core.mapbox_boundaries_reverse_enrich(
  DB_NAME STRING,
  SCHEMA_NAME STRING,
  TABLE_NAME STRING,
  DESTINATION_COLUMN_NAME STRING,
  INCREMENTAL BOOLEAN,
  SOURCE_LONGITUDE_COLUMN_NAME VARCHAR,
  SOURCE_LATITUDE_COLUMN_NAME VARCHAR,
  PARAM_BOUNDARIES_SET VARCHAR,
  PARAM_WORLDVIEW VARCHAR
)
```

- DB_NAME - the name of the database to operate on
- SCHEMA_NAME - the name of the schema to operate on
- TABLE_NAME - the name of the table to operate on
- DESTINATION_COLUMN_NAME - the name of the column in which to write the result of the layer lookup
- INCREMENTAL BOOLEAN - if true, the procedure will only update rows that have a null value in the specified destination column
- SOURCE_LONGITUDE_COLUMN_NAME - the column name that contains the longitude values used for the lookup
- SOURCE_LATITUDE_COLUMN_NAME - the column name that contains the latitude values used for the loopup
- PARAM_BOUNDARIES_SET - the set of boundaries layers to look up. Must be either 'basic' or 'detailed'. "basic" boundaries layers include: 'adm0', 'adm1', 'adm2', 'loc1', 'loc2', 'loc3', 'loc4', 'pos1', 'pos2', 'pos3', and 'pos4'. "detailed" boundaries layers include any layer that is not listed as a "basic" layer.
- PARAM_WORLDVIEW - the worldview to use. For now, only 'US' is supported

##### Examples

The below example uses a sample schema and table that comes with the Mapbox app. It uses:

- The database called "mapbox"
- The schema in that same database called "sample_data"
- A table in that schema called "sample_points"
- A column called "BOUNDARIES_BASIC" in that same table which you wish to populate with boundaries information
- A column in that same table called "longitude" which contains the longitude point to use for the lookup
- A column in that same table called "latitude" which contains the latitude point to use for the lookup

This stored procedure call will populate the provided table in-place with boundaries data in the specified destination column

```
CALL mapbox.core.mapbox_boundaries_reverse_enrich(
  'mapbox',
  'sample_data',
  'sample_points',
  'BOUNDARIES_BASIC',
  false,
  'longitude',
  'latitude',
  'basic',
  null
)
```

Keep in mind that you must grant access to allow the application to access databases, schemas, and tables within your Snowflake account. The below example assumes you have a database called "mydatabase" with a schema called "testing", and a table called "sample_points".

```
GRANT USAGE ON DATABASE mydatabase to application mapbox
GRANT USAGE ON SCHEMA mydatabase.testing to application mapbox
GRANT SELECT ON TABLE mydatabase.testing.sample_points to application mapbox
GRANT UPDATE ON TABLE mydatabase.testing.sample_points to application mapbox
```

## General tips

### Using response values

Responses to geocoding stored procedures as well as responses returned from the boundaries stored procedure are in JSON format. You can [read more here](https://docs.snowflake.com/en/user-guide/querying-semistructured) about how to access properties within JSON reponses. Below are some specific examples.

#### Access a specific property

Take the following example JSON response, which is the same structure that would be in the sample_data.geocode_reverse table if you ran the geocode_reverse_enrich example above:

```
{
  "accuracy": "rooftop",
  "confidence": "exact",
  "context": {
    "country": {
      "country_code": "US",
      "country_code_alpha_3": "USA",
      "mapbox_id": "dXJuOm1ieHBsYzpJdXc",
      "name": "United States",
      "wikidata_id": "Q30"
    },
    "district": {
      "mapbox_id": "dXJuOm1ieHBsYzpudWJz",
      "name": "Hillsborough County",
      "wikidata_id": "Q488874"
    },
    "neighborhood": {
      "mapbox_id": "dXJuOm1ieHBsYzpEWW1NN0E",
      "name": "Fountain Square"
    },
    "place": {
      "alternate": {
        "mapbox_id": "dXJuOm1ieHBsYzpFTkRvN0E",
        "name": "Rocky Point"
      },
      "mapbox_id": "dXJuOm1ieHBsYzpFejVJN0E",
      "name": "Tampa",
      "wikidata_id": "Q49255"
    },
    "postcode": {
      "mapbox_id": "dXJuOm1ieHBsYzpCc0J1N0E",
      "name": "33607"
    },
    "region": {
      "mapbox_id": "dXJuOm1ieHBsYzpCZVRz",
      "name": "Florida",
      "region_code": "FL",
      "region_code_full": "US-FL",
      "wikidata_id": "Q812"
    }
  },
  "feature_type": "address",
  "latitude": 27.97981,
  "longitude": -82.534586,
  "mapbox_id": "dXJuOm1ieGFkcjo5ZTQzZGI5Ni1mNzhkLTQ1MGEtOTEwYy0wYTM3ZDMyNmMxMzg",
  "name": "4100 George J. Bean Parkway",
  "place_formatted": "Tampa, Florida 33607, United States"
}
```

You can access a specific property in the JSON response like the following:

```
SELECT response:name from mapbox.sample_data.geocode_forward;
```

This will return only the value of the "name" property in the JSON response.

If the property is multiple levels deep in the JSON hierarchy, such as the "country_code" beneath the country property, which is beneath the context object, you can do:

```
SELECT response:context:country:country_code from mapbox.sample_data.geocode_forward;
```

## Version and upgrade notes

Earlier versions of the application included user-defined functions (UDFs) for accessing geocoding functionality. These UDFs have been replaced with stored procedures. This table shows the name of the stored procedures that supercede each UDF

old UDF name | new stored procedure name
----------|----------------------
geocode_forward | geocode_forward_enrich
geocode_reverse | geocode_reverse_enrich
geocode_structured | geocode_structured_enrich


## Conclusion And Resources

Congratulations! You've successfully completed the Getting Started with Mapbox Geocoding & Analysis Tools quickstart guide.

What You Learned
- How to install the Mapbox Geocoding & Analysis Tools Native App
- How to use functions in the the Mapbox Geocoding & Analysis Tools Native App

Related Resources
- [Geocoding API](https://docs.mapbox.com/api/search/geocoding)
- [Geocoding API Playground](https://docs.mapbox.com/playground/geocoding)
