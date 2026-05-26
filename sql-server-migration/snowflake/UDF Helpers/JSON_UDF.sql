-- <copyright file="JSON_UDF.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2025 Snowflake Inc. All rights reserved.
-- </copyright>

-- =========================================================================================================
-- Description: Used to trim a SQL Server JSON path to generate its Snowflake equivalent.
-- Parameters:
--     path: The JSON path to be processed.
-- Returns:
--     A string with the processed JSON path.
-- Example:
--     Input: SELECT PUBLIC.GET_PROCESSED_PATH_UDF('strict $.members[0].name');
--     Output: 'members[0].name'
-- =========================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.GET_PROCESSED_PATH_UDF(path STRING)
RETURNS STRING
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    REGEXP_REPLACE(path, '.*\\$\\.?')
$$;

-- =========================================================================================================
-- Description: Validates if the JSON path contains one of the SQL Server JSON path flags.
-- Parameters:
--     path: The JSON path to be processed.
--     flagName: The name of the flag to check for.
-- Returns:
--     A boolean indicating if the path contains the flag.
-- Example:
--     Input: SELECT PUBLIC.PATH_CONTAINS_FLAG_UDF('strict $.members[0].name', 'STRICT');
--     Output: TRUE
--     Input: SELECT PUBLIC.PATH_CONTAINS_FLAG_UDF('strict $.members[0].name', 'APPEND');
--     Output: FALSE
-- =========================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.PATH_CONTAINS_FLAG_UDF(path STRING, flagName STRING)
RETURNS BOOLEAN
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    CONTAINS(UPPER(TRIM(SPLIT_PART(path, '$', 1))), flagName)
$$;

-- =========================================================================================================
-- Description: Checks the JSON value obtained from the path to ensure it is of the expected type.
--              Used to emulate the STRICT mode of SQL Server JSON functions.
-- Parameters:
--     value: The value extracted from the JSON object.
--     isStrict: A boolean indicating if strict mode is enabled.
--     objectExpected: A boolean indicating if the value is expected to be an object.
-- Returns:
--     If the JSON value is valid, it returns the value; otherwise, it throws an error.
-- Example:
--     Input: SELECT PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF(PARSE_JSON('{"name": "John"}'), TRUE, TRUE);
--     Output: '{"name": "John"}'
--     Input: SELECT PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF(PARSE_JSON('{"name": "John"}'), TRUE, FALSE);
--     Output: Exception: "Extracted value is of invalid type"
--     Input: SELECT PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF(PARSE_JSON('{"name": "John"}'), FALSE, FALSE);
--     Output: NULL
--     Input: SELECT PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF(TO_VARIANT(10), TRUE, FALSE);
--     Output: 10
-- =========================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF(value VARIANT, isStrict BOOLEAN, objectExpected BOOLEAN)
RETURNS VARIANT
LANGUAGE JAVASCRIPT
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    const jsonType = typeof VALUE;
    if (jsonType === 'undefined' && ISSTRICT) {
        throw "Property not found";
    }

    const isObjectValue = jsonType === 'object';
    if (isObjectValue == OBJECTEXPECTED) {
        return VALUE;
    }

    if (!ISSTRICT) {
        return undefined;
    }

    throw "Extracted value is of invalid type";
$$;

-- =========================================================================================================
-- Description: Emulates the way the SQL Server OPENJSON function classifies JSON values by type.
--              Used to generated the TYPE column for the OPENJSON result table when no schema is provided.
-- Parameters:
--     value: The JSON value to get its type from.
-- Returns:
--     An integer representing the data type of the JSON value.
-- Example:
--     Input: SELECT PUBLIC.GET_OPENJSON_DATATYPE_UDF(PARSE_JSON('{"name": "John"}'));
--     Output: 5 (Object)
--     Input: SELECT PUBLIC.GET_OPENJSON_DATATYPE_UDF(PARSE_JSON('["apple", "banana"]'));
--     Output: 4 (Array)
--     Input: SELECT PUBLIC.GET_OPENJSON_DATATYPE_UDF(PARSE_JSON('123'));
--     Output: 2 (Integer)
-- =========================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.GET_OPENJSON_DATATYPE_UDF(value VARIANT)
RETURNS INTEGER
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    DECODE(
        TYPEOF(value),
        'VARCHAR', 1,
        'INTEGER', 2,
        'DECIMAL', 2,
        'DOUBLE', 2,
        'BOOLEAN', 3,
        'ARRAY', 4,
        'OBJECT', 5,
        0)
$$;

-- ===============================================================================================================
-- Description: Replicates the OPENJSON function behavior from SQL Server in Snowflake when no schema is provided.
-- Parameters:
--     json_string: String containing the JSON object.
--     json_path: The path at which the JSON object is to be processed.
-- Returns:
--     A table with the keys, values, and types of the JSON object.
-- Example:
--     Input: SELECT * FROM TABLE(OPENJSON_UDF('{"name": "John", "age": 30, "isActive": true, "cars": [{"brand": "Honda", "year": 2000}, {"brand": "BYD", "year":2024}]}'));
--     Output: 
--     +----------+-------------------------------------------------------------+------+
--     | KEY      | VALUE                                                       | TYPE |
--     +----------+-------------------------------------------------------------+------+
--     | age      | 30                                                          | 2    |
--     | cars     | [{"brand":"Honda","year":2000},{"brand":"BYD","year":2024}] | 4    |
--     | isActive | true                                                        | 3    |
--     | name     | John                                                        | 1    |
--     +----------+-------------------------------------------------------------+------+
--     Input: SELECT * FROM TABLE(OPENJSON_UDF('{"name": "John", "age": 30, "isActive": true, "cars": [{"brand": "Honda", "year": 2000}, {"brand": "BYD", "year":2024}]}', '$.cars'));
--     Output: 
--     +-----+-------------------------------+------+
--     | KEY | VALUE                         | TYPE |
--     +-----+-------------------------------+------+
--     | 0   | {"brand":"Honda","year":2000} | 5    |
--     | 1   | {"brand":"BYD","year":2024}   | 5    |
--     +-----+-------------------------------+------+
-- ===============================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.OPENJSON_UDF(json_string STRING, json_path STRING DEFAULT '')
RETURNS TABLE (key STRING, value STRING, type INTEGER)
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    SELECT
        NVL(key, TO_VARCHAR(index)),
        TO_VARCHAR(value),
        PUBLIC.GET_OPENJSON_DATATYPE_UDF(value)
    FROM TABLE(FLATTEN(INPUT => PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF
                                    (
                                        IFF(PUBLIC.GET_PROCESSED_PATH_UDF(json_path) = '', PARSE_JSON(json_string), GET_PATH(PARSE_JSON(json_string), PUBLIC.GET_PROCESSED_PATH_UDF(json_path))),
                                        PUBLIC.PATH_CONTAINS_FLAG_UDF(json_path, 'STRICT'),
                                        TRUE
                                    )))
$$;

-- ==============================================================================================================
-- Description: Replicates the OPENJSON function behavior from SQL Server in Snowflake when a schema is provided.
-- Parameters:
--     json_string: String containing the JSON object.
--     start_path: The path at which the JSON object is to be processed.
--     column_schema: A variant containing the schema of the columns to be extracted.
--                    It should be an array of objects with the 'Name' and 'Path' properties for each column.
-- Returns:
--     An array of objects representing the extracted JSON data. This array will be used to create a result set.
--     To complete the transformation, the output of this function will be used in a subquery that forms the final table.
-- Example:
--     Input: SELECT TABLE(PUBLIC.OPENJSON_WITH_SCHEMA_UDF('{
--             "Order": {
--                 "Number": "SO43659",
--                 "Date": "2011-05-31T00:00:00"
--             },
--             "AccountNumber": "AW29825",
--             "Item": {
--                 "Price": 2024.9940,
--                 "Quantity": 1
--             }
--         }', '', PARSE_JSON('[
--              {
--                  "Name": "Number",
--                  "Path": "$.Order.Number"
--              },
--              {
--                  "Name": "Date",
--                  "Path": "$.Order.Date"
--              },
--              {
--                  "Name": "Customer",
--                  "Path": "$.AccountNumber"
--              },
--              {
--                  "Name": "Quantity",
--                  "Path": "$.Item.Quantity"
--              },
--              {
--                  "Name": "Order",
--                  "Path": "Order"
--              }
--          ]')));
--     Output:
--     [
--       {
--         "Customer": "AW29825",
--         "Date": "2011-05-31T00:00:00",
--         "Number": "SO43659",
--         "Order": {
--           "Date": "2011-05-31T00:00:00",
--           "Number": "SO43659"
--         },
--         "Quantity": 1
--       }
--     ]
-- ==============================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.OPENJSON_WITH_SCHEMA_UDF(json_string STRING, start_path STRING, column_schema VARIANT)
RETURNS VARIANT
LANGUAGE JAVASCRIPT
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    function getPathData(originalPath) {
        let trimmedPath = originalPath.trim();
        let isStrict = false;
        const dollarPosition = trimmedPath.indexOf("$");
        if (dollarPosition === -1)
        {
            return { path: trimmedPath, isStrict };
        }

        const options = trimmedPath.substring(0, dollarPosition);
        let path = trimmedPath[dollarPosition + 1] === "."
                 ? trimmedPath.substring(dollarPosition + 2)
                 : trimmedPath.substring(dollarPosition + 1);
        isStrict = options.toLowerCase().startsWith("strict");
        return { path, isStrict };
    }

    const getValueByPath = (obj, path, isStrict) => {
        return path.split('.').reduce((current, key) => {
            if (current && typeof current === 'object' && key in current) {
                return current[key];
            }
            
            if (isStrict)
            {
                throw "Property not found";
            }
            
            return undefined;
        }, obj);
    };
    const baseJson = JSON.parse(JSON_STRING);
    const pathData = getPathData(START_PATH);
    const sourceData = pathData.path === '' ? baseJson : getValueByPath(baseJson, pathData.path, pathData.isStrict);
    if (sourceData === undefined)
    {
        return undefined;
    }

    const dataArray = Array.isArray(sourceData) ? sourceData : [sourceData];
    const extractedResult = [];
    for (const item of dataArray){
        const currentResult = {};
        for (const { Name, Path } of COLUMN_SCHEMA) {
            const pathInfo = getPathData(Path);
            const value = getValueByPath(item, pathInfo.path, pathInfo.isStrict);
            currentResult[Name] = value;
        }

        extractedResult.push(currentResult);
    }

    return extractedResult;
$$;

-- ==============================================================================================================
-- Description: Used to update or delete a property from a JSON object.
--              Used by JSON_MODIFY_UDF to replicate the JSON_MODIFY function from SQL Server.
-- Parameters:
--     json_string: String containing the JSON object.
--     path: The path at which the property is located.
--     newValue: The new value to set for the property. If undefined, the property will be deleted.
--     isStrict: A boolean indicating if strict mode is enabled.
--               If true, an error will be thrown if the property does not exist.
--     appendFlag: A boolean indicating if the property is an array and the new value should be appended to it.
--                 If false, the property will be replaced or deleted.
-- Returns:
--     A string containing the updated JSON object.
-- Example:
--     Input: SELECT PUBLIC.UPDATE_JSON_UDF('{"name": "John", "age": 30}', 'name', 'Jane', TRUE, FALSE);
--     Output: '{"name": "Jane", "age": 30}'
--     Input: SELECT PUBLIC.UPDATE_JSON_UDF('{"name": "John", "age": 30}', 'age', NULL, TRUE, FALSE);
--     Output: '{"name": "John"}'
--     Input: SELECT PUBLIC.UPDATE_JSON_UDF('{"name": "John", "age": 30, "hobbies": ["hiking"]}', 'hobbies', 'reading', FALSE, FALSE);
--     Output: {"name": "John", "age": 30, "hobbies": ["hiking", "reading"]}
-- ==============================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.UPDATE_JSON_UDF(json_string STRING, path STRING, newValue STRING, isStrict BOOLEAN, appendFlag BOOLEAN)
RETURNS STRING
LANGUAGE JAVASCRIPT
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    const pathParts = PATH.replace(/\[(\d+)\]/g, '.$1').split('.');
    let result = JSON.parse(JSON_STRING);
    let current = result;
    for (let i = 0; i < pathParts.length; i++) {
        const key = pathParts[i];
        if (typeof current[key] === 'undefined' || current[key] === null) {
            if (ISSTRICT) {
                throw "Property does not exist";
            }

            const nextKey = pathParts[i+1];
            current[key] = /^\d+$/.test(nextKey) ? [] : {};
        }

        if (i < pathParts.length - 1) {
            current = current[key];
        }
    }

    const finalKey = pathParts[pathParts.length - 1];
    if (APPENDFLAG) {
        if (Array.isArray(current[finalKey])) {
            current[finalKey].push(NEWVALUE);
        } else if (ISSTRICT) {
            throw "Property is not an array";
        }
    } else if (NEWVALUE !== undefined) {
        current[finalKey] = NEWVALUE;
    } else {
        delete current[finalKey];
    }

    return JSON.stringify(result);
$$;

-- ==============================================================================================================
-- Description: Used to update or remove a property from a JSON object.
--              Replicates the JSON_MODIFY function from SQL Server.
-- Parameters:
--     json_string: String containing the JSON object.
--     path: The path at which the property is located.
--     newValue: The new value to set for the property. If undefined, the property will be deleted.
-- Returns:
--     A string containing the updated JSON object.
-- Example:
--     Input: SELECT PUBLIC.JSON_MODIFY_UDF('{"name": "John", "age": 30}', '$.name', 'Jane');
--     Output: '{"name": "Jane", "age": 30}'
--     Input: SELECT PUBLIC.JSON_MODIFY_UDF('{"name": "John", "age": 30}', '$.age', NULL);
--     Output: '{"name": "John"}'
--     Input: SELECT PUBLIC.JSON_MODIFY_UDF('{"name": "John", "age": 30, "hobbies": ["hiking"]}', 'append $.hobbies', 'reading');
--     Output: '{"name": "John", "age": 30, "hobbies": ["hiking", "reading"]}'
-- ==============================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.JSON_MODIFY_UDF(json_string STRING, path STRING, newValue STRING)
RETURNS STRING
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    PUBLIC.UPDATE_JSON_UDF(json_string, PUBLIC.GET_PROCESSED_PATH_UDF(path), newValue, PUBLIC.PATH_CONTAINS_FLAG_UDF(path, 'STRICT'), PUBLIC.PATH_CONTAINS_FLAG_UDF(path, 'APPEND'))
$$;

-- ==============================================================================================================
-- Description: Obtains a value from a JSON object.
--              Replicates the JSON_VALUE and JSON_QUERY functions from SQL Server.
-- Parameters:
--     json_string: String containing the JSON object.
--     path: The path at which the property is located.
--     objectExpected: A boolean indicating if the extracted value is expected to be an object.
-- Returns:
--     A string containing the extracted JSON value.
-- Example:
--     Input: SELECT PUBLIC.GET_JSON_VALUE_UDF('{"name": "John", "age": 30}', '$.name', FALSE);
--     Output: 'John'
--     Input: SELECT PUBLIC.GET_JSON_VALUE_UDF('{"name": "John", "age": 30}', '$.age', TRUE);
--     Output: NULL
--     Input: SELECT PUBLIC.GET_JSON_VALUE_UDF('{"name": "John", "age": 30}', 'strict $.age', TRUE);
--     Output: Exception: "Extracted value is of invalid type"
--     Input: SELECT PUBLIC.GET_JSON_VALUE_UDF('{"name": "John", "age": 30, "details": {"city": "New York"}}', '$.details', TRUE);
--     Output: '{"city": "New York"}'
-- ==============================================================================================================
CREATE OR REPLACE FUNCTION PUBLIC.GET_JSON_VALUE_UDF(json_string STRING, path STRING, objectExpected BOOLEAN)
RETURNS STRING
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    TO_VARCHAR(PUBLIC.VALIDATE_EXTRACTED_JSON_VALUE_UDF(
                    IFF(PUBLIC.GET_PROCESSED_PATH_UDF(path) != '', GET_PATH(PARSE_JSON(json_string), PUBLIC.GET_PROCESSED_PATH_UDF(path)), PARSE_JSON(json_string)),
                    PUBLIC.PATH_CONTAINS_FLAG_UDF(path, 'STRICT'),
                    objectExpected))
$$;