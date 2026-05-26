USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 2. fn_ParseTruckConfigJSON — scalar UDF
--    Converted from multi-statement TVF to scalar. Returns the count of
--    operational equipment items declared in the truck's JSON config.
--    Returns 0 when TruckConfig is NULL or the truck does not exist.
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION TastyBytes.fn_ParseTruckConfigJSON (TRUCKID INT)
RETURNS INT
LANGUAGE SQL
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    WITH CTE1 AS
    (

        SELECT
            COUNT(*) AS EQUIPMENTCOUNT
        FROM
            TastyBytes.FoodTruck ft
            !!!RESOLVE EWI!!! /*** SSC-EWI-TS0082 - CROSS APPLY HAS BEEN CONVERTED TO LEFT OUTER JOIN AND REQUIRES MANUAL VALIDATION. ***/!!!
            LEFT OUTER JOIN
                TABLE(PUBLIC.OPENJSON_UDF(ft.TruckConfig, '$.Equipment')) e
        WHERE
            ft.TruckID = TRUCKID
          AND ft.TruckConfig IS NOT NULL
          AND CAST(GET_PATH(PARSE_JSON(e.value), 'IsOperational') AS BOOLEAN) = 1
    )
    SELECT
        NVL(EQUIPMENTCOUNT, 0)
    FROM
        CTE1
$$;