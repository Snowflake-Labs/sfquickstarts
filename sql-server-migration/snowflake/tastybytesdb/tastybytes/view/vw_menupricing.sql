USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 3. vw_MenuPricing
--    EWI triggers: TS0010 (CTE in view)
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW TastyBytes.vw_MenuPricing
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
--** SSC-PRF-TS0001 - PERFORMANCE WARNING - RECURSION FOR CTE NOT CHECKED. MIGHT REQUIRE RECURSIVE KEYWORD **
WITH MenuStats AS (
    SELECT
        m.MenuID,
        m.MenuName,
        m.CuisineType,
        COUNT(mi.MenuItemID)             AS ItemCount,
        MIN(mi.BasePrice)                AS MinPrice,
        MAX(mi.BasePrice)                AS MaxPrice,
        AVG(mi.BasePrice)                AS AvgPrice
    FROM
        TastyBytes.Menu m
    INNER JOIN
            TastyBytes.MenuItem mi
            ON m.MenuID = mi.MenuID
    GROUP BY
        m.MenuID,
        m.MenuName,
        m.CuisineType
)
SELECT
    ms.MenuID,
    ms.MenuName,
    ms.CuisineType,
    ms.ItemCount,
    ms.MinPrice,
    ms.MaxPrice,
    ms.AvgPrice,
    (ms.MaxPrice - ms.MinPrice) AS PriceRange
FROM
    MenuStats ms;