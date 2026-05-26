USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 1. vw_ActiveTrucks
--    EWI triggers: TS0044 (NOLOCK table hints)
-- --------------------------------------------------------------------------
CREATE VIEW TastyBytes.vw_ActiveTrucks
AS
SELECT
    ft.TruckID,
    ft.TruckName,
    ft.LicensePlate,
    c.CityName,
    co.CountryName,
    ft.YearPurchased,
    ft.MaxCapacity
FROM TastyBytes.FoodTruck ft WITH (NOLOCK)
INNER JOIN TastyBytes.City c WITH (NOLOCK) ON ft.CityID = c.CityID
INNER JOIN TastyBytes.Country co WITH (NOLOCK) ON c.CountryID = co.CountryID
WHERE ft.IsOperational = 1