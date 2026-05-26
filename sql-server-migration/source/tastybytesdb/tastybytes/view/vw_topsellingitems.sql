USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 4. vw_TopSellingItems — CROSS APPLY
-- --------------------------------------------------------------------------
CREATE VIEW TastyBytes.vw_TopSellingItems
AS
SELECT
    ft.TruckID,
    ft.TruckName,
    TopItems.MenuItemID,
    TopItems.ItemName,
    TopItems.TotalQuantitySold,
    TopItems.TotalRevenue
FROM TastyBytes.FoodTruck ft
CROSS APPLY (
    SELECT TOP 5
        mi.MenuItemID,
        mi.ItemName,
        SUM(od.Quantity)                 AS TotalQuantitySold,
        SUM(od.Quantity * od.UnitPrice)  AS TotalRevenue
    FROM TastyBytes.OrderDetail od
    INNER JOIN TastyBytes.OrderHeader oh ON od.OrderID = oh.OrderID
    INNER JOIN TastyBytes.MenuItem mi ON od.MenuItemID = mi.MenuItemID
    WHERE oh.TruckID = ft.TruckID
      AND oh.OrderStatus = 'Completed'
    GROUP BY mi.MenuItemID, mi.ItemName
    ORDER BY SUM(od.Quantity) DESC
) TopItems