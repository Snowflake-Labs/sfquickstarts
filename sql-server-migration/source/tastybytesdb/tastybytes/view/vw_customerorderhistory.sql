USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 5. vw_CustomerOrderHistory
-- --------------------------------------------------------------------------
CREATE VIEW TastyBytes.vw_CustomerOrderHistory
AS
SELECT TOP 1000
    cu.CustomerID,
    cu.FirstName + ' ' + cu.LastName    AS CustomerName,
    cu.Email,
    cu.LoyaltyPoints,
    oh.OrderID,
    oh.OrderDate,
    oh.TotalAmount,
    oh.OrderStatus,
    ft.TruckName
FROM TastyBytes.Customer cu
INNER JOIN TastyBytes.OrderHeader oh ON cu.CustomerID = oh.CustomerID
INNER JOIN TastyBytes.FoodTruck ft ON oh.TruckID = ft.TruckID
ORDER BY oh.OrderDate DESC