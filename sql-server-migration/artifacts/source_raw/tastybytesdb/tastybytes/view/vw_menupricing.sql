USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 3. vw_MenuPricing
--    EWI triggers: TS0010 (CTE in view)
-- --------------------------------------------------------------------------
CREATE VIEW TastyBytes.vw_MenuPricing
AS
WITH MenuStats AS (
    SELECT
        m.MenuID,
        m.MenuName,
        m.CuisineType,
        COUNT(mi.MenuItemID)             AS ItemCount,
        MIN(mi.BasePrice)                AS MinPrice,
        MAX(mi.BasePrice)                AS MaxPrice,
        AVG(mi.BasePrice)                AS AvgPrice
    FROM TastyBytes.Menu m
    INNER JOIN TastyBytes.MenuItem mi ON m.MenuID = mi.MenuID
    GROUP BY m.MenuID, m.MenuName, m.CuisineType
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
FROM MenuStats ms