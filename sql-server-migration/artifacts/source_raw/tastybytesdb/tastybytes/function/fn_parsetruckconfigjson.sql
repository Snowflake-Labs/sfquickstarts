USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 2. fn_ParseTruckConfigJSON — scalar UDF
--    Converted from multi-statement TVF to scalar. Returns the count of
--    operational equipment items declared in the truck's JSON config.
--    Returns 0 when TruckConfig is NULL or the truck does not exist.
-- --------------------------------------------------------------------------
CREATE FUNCTION TastyBytes.fn_ParseTruckConfigJSON
(
    @TruckID INT
)
RETURNS INT
AS
BEGIN
    DECLARE @EquipmentCount INT;

    SELECT @EquipmentCount = COUNT(*)
    FROM TastyBytes.FoodTruck ft
    CROSS APPLY OPENJSON(ft.TruckConfig, '$.Equipment') e
    WHERE ft.TruckID = @TruckID
      AND ft.TruckConfig IS NOT NULL
      AND CAST(JSON_VALUE(e.value, '$.IsOperational') AS BIT) = 1;

    RETURN ISNULL(@EquipmentCount, 0);
END