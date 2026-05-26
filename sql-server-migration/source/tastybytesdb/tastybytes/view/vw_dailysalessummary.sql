USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 2. vw_DailySalesSummary
--    EWI triggers: TS0044 (NOLOCK table hint)
-- --------------------------------------------------------------------------
CREATE VIEW TastyBytes.vw_DailySalesSummary
AS
SELECT
    CAST(oh.OrderDate AS DATE)          AS SaleDate,
    ft.TruckName,
    c.CityName,
    COUNT(*)                             AS TotalOrders,
    SUM(oh.TotalAmount)                  AS GrossRevenue,
    SUM(oh.TipAmount)                    AS TotalTips,
    AVG(oh.TotalAmount)                  AS AvgOrderValue
FROM TastyBytes.OrderHeader oh WITH (NOLOCK)
INNER JOIN TastyBytes.FoodTruck ft WITH (NOLOCK) ON oh.TruckID = ft.TruckID
INNER JOIN TastyBytes.City c ON ft.CityID = c.CityID
WHERE oh.OrderStatus = 'Completed'
GROUP BY CAST(oh.OrderDate AS DATE), ft.TruckName, c.CityName