USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 5. vw_CustomerOrderHistory
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW TastyBytes.vw_CustomerOrderHistory
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
SELECT TOP 1000
    cu.CustomerID,
    cu.FirstName || ' ' || cu.LastName AS CustomerName,
    cu.Email,
    cu.LoyaltyPoints,
    oh.OrderID,
    oh.OrderDate,
    oh.TotalAmount,
    oh.OrderStatus,
    ft.TruckName
FROM
    TastyBytes.Customer cu
INNER JOIN
        TastyBytes.OrderHeader oh
        ON cu.CustomerID = oh.CustomerID
INNER JOIN
        TastyBytes.FoodTruck ft
        ON oh.TruckID = ft.TruckID
ORDER BY oh.OrderDate DESC;