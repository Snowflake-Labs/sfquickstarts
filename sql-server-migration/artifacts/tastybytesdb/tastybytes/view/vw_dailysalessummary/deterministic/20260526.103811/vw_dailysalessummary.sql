USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 2. vw_DailySalesSummary
--    EWI triggers: TS0044 (NOLOCK table hint)
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW TastyBytes.vw_DailySalesSummary
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
SELECT
    TO_TIMESTAMP_NTZ(oh.OrderDate) AS SaleDate,
    ft.TruckName,
    c.CityName,
    COUNT(*)                             AS TotalOrders,
    SUM(oh.TotalAmount)                  AS GrossRevenue,
    SUM(oh.TipAmount)                    AS TotalTips,
    AVG(oh.TotalAmount)                  AS AvgOrderValue
FROM
    TastyBytes.OrderHeader oh
INNER JOIN
        TastyBytes.FoodTruck ft
        ON oh.TruckID = ft.TruckID
INNER JOIN
        TastyBytes.City c
        ON ft.CityID = c.CityID
WHERE
    oh.OrderStatus = 'Completed'
GROUP BY
    TO_TIMESTAMP_NTZ(oh.OrderDate),
    ft.TruckName,
    c.CityName;