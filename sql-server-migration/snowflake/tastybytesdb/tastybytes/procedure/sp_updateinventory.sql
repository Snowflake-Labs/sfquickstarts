USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 1. sp_UpdateInventory
--    Restocks inventory items at/below ReorderLevel for a given truck.
--    Returns ItemsRestocked = count of rows updated.
--    Optional @AsOf parameter makes LastRestocked deterministic for testing.
-- --------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE TastyBytes.sp_UpdateInventory (TRUCKID INT DEFAULT NULL, ASOF TIMESTAMP_NTZ(3) DEFAULT NULL)
RETURNS ARRAY
LANGUAGE SQL
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
EXECUTE AS CALLER

-- Short-circuit on NULL so the predicate never relies on UNKNOWN semantics
AS
$$
    DECLARE
        RESTOCKCOUNT INT := 0;
        ProcedureResultSet1 VARCHAR;
        ProcedureResultSet2 VARCHAR;
        return_arr ARRAY := array_construct();
    BEGIN
--        --** SSC-FDM-TS0029 - SET NOCOUNT STATEMENT IS COMMENTED OUT, WHICH IS NOT APPLICABLE IN SNOWFLAKE. **
--        SET NOCOUNT ON;
        IF (:TRUCKID IS NULL) THEN
            ProcedureResultSet1 := 'RESULTSET_' || REPLACE(UPPER(UUID_STRING()), '-', '_');
            CREATE OR REPLACE TEMPORARY TABLE IDENTIFIER(:ProcedureResultSet1) AS
                SELECT 0 AS ItemsRestocked;
            return_arr := array_append(return_arr, :ProcedureResultSet1);
            RETURN NULL;
        END IF;

        UPDATE TastyBytes.Inventory
        SET
                QuantityOnHand = ReorderLevel * 2,
                LastRestocked = COALESCE(:ASOF, CURRENT_TIMESTAMP() :: TIMESTAMP)
        WHERE
                TruckID = :TRUCKID
          AND QuantityOnHand <= ReorderLevel;
        RESTOCKCOUNT := SQLROWCOUNT;
        ProcedureResultSet2 := 'RESULTSET_' || REPLACE(UPPER(UUID_STRING()), '-', '_');
        CREATE OR REPLACE TEMPORARY TABLE IDENTIFIER(:ProcedureResultSet2) AS
            SELECT
                :RESTOCKCOUNT AS ItemsRestocked;
        return_arr := array_append(return_arr, :ProcedureResultSet2);
        --** SSC-FDM-0020 - MULTIPLE RESULT SETS ARE RETURNED IN TEMPORARY TABLES **
        RETURN return_arr;
    END;
$$;