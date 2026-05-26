USE TastyBytesDB;
GO
-- --------------------------------------------------------------------------
-- 1. sp_UpdateInventory
--    Restocks inventory items at/below ReorderLevel for a given truck.
--    Returns ItemsRestocked = count of rows updated.
--    Optional @AsOf parameter makes LastRestocked deterministic for testing.
-- --------------------------------------------------------------------------
CREATE PROCEDURE TastyBytes.sp_UpdateInventory
    @TruckID  INT      = NULL,
    @AsOf     DATETIME = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @RestockCount INT = 0;

    -- Short-circuit on NULL so the predicate never relies on UNKNOWN semantics
    IF @TruckID IS NULL
    BEGIN
        SELECT 0 AS ItemsRestocked;
        RETURN;
    END

    UPDATE TastyBytes.Inventory
    SET QuantityOnHand = ReorderLevel * 2,
        LastRestocked  = COALESCE(@AsOf, GETDATE())
    WHERE TruckID       = @TruckID
      AND QuantityOnHand <= ReorderLevel;

    SET @RestockCount = @@ROWCOUNT;

    SELECT @RestockCount AS ItemsRestocked;
END;