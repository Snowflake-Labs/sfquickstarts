USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 4. vw_TopSellingItems — CROSS APPLY
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW TastyBytes.vw_TopSellingItems
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
SELECT
    ft.TruckID,
    ft.TruckName,
    TopItems.MenuItemID,
    TopItems.ItemName,
    TopItems.TotalQuantitySold,
    TopItems.TotalRevenue
FROM
    TastyBytes.FoodTruck ft
    !!!RESOLVE EWI!!! /*** SSC-EWI-TS0082 - CROSS APPLY HAS BEEN CONVERTED TO LEFT OUTER JOIN AND REQUIRES MANUAL VALIDATION. ***/!!!
    LEFT OUTER JOIN
        (
               SELECT TOP 5
                   mi.MenuItemID,
                   mi.ItemName,
                   SUM(od.Quantity)                 AS TotalQuantitySold,
                   SUM(od.Quantity * od.UnitPrice)  AS TotalRevenue
               FROM
                   TastyBytes.OrderDetail od
               INNER JOIN
                       TastyBytes.OrderHeader oh
                       ON od.OrderID = oh.OrderID
               INNER JOIN
                       TastyBytes.MenuItem mi
                       ON od.MenuItemID = mi.MenuItemID
               WHERE
                   oh.TruckID = ft.TruckID
                 AND oh.OrderStatus = 'Completed'
               GROUP BY
                   mi.MenuItemID,
                   mi.ItemName
               ORDER BY SUM(od.Quantity) DESC
           ) TopItems;