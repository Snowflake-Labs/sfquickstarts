USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 1. vw_ActiveTrucks
--    EWI triggers: TS0044 (NOLOCK table hints)
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW TastyBytes.vw_ActiveTrucks
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
SELECT
    ft.TruckID,
    ft.TruckName,
    ft.LicensePlate,
    c.CityName,
    co.CountryName,
    ft.YearPurchased,
    ft.MaxCapacity
FROM
    TastyBytes.FoodTruck ft
INNER JOIN
        TastyBytes.City c
        ON ft.CityID = c.CityID
INNER JOIN
        TastyBytes.Country co
        ON c.CountryID = co.CountryID
WHERE
    ft.IsOperational = 1;