USE DATABASE TastyBytesDB;

-- --------------------------------------------------------------------------
-- 1. fn_FormatPhoneNumber — STUFF, PATINDEX
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION TastyBytes.fn_FormatPhoneNumber (RAWPHONE STRING)
RETURNS VARCHAR(20)
LANGUAGE SQL
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "transact",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
    DECLARE
        CLEANPHONE VARCHAR(20);
        FORMATTED VARCHAR(20);
    BEGIN
         
         

        -- Strip non-numeric characters
        CLEANPHONE := :RAWPHONE;
        WHILE (PUBLIC.PATINDEX_UDF('%[^0-9]%', :CLEANPHONE) !!!RESOLVE EWI!!! /*** SSC-EWI-0021 - INVOCATION OF 'PUBLIC.PATINDEX_UDF' HELPER INSIDE A SNOWSCRIPT UDF NOT SUPPORTED IN SNOWFLAKE ***/!!! > 0) LOOP
            CLEANPHONE := INSERT(:CLEANPHONE, PUBLIC.PATINDEX_UDF('%[^0-9]%', :CLEANPHONE) !!!RESOLVE EWI!!! /*** SSC-EWI-0021 - INVOCATION OF 'PUBLIC.PATINDEX_UDF' HELPER INSIDE A SNOWSCRIPT UDF NOT SUPPORTED IN SNOWFLAKE ***/!!!, 1, '');
            IF (LEN(:CLEANPHONE) = 10) THEN
                FORMATTED := '(' || LEFT(:CLEANPHONE, 3) || ') ' || SUBSTRING(:CLEANPHONE, 4, 3) || '-' || RIGHT(:CLEANPHONE, 4);
            ELSEIF (LEN(:CLEANPHONE) = 11) THEN
                FORMATTED := '+' || LEFT(:CLEANPHONE, 1) || ' (' || SUBSTRING(:CLEANPHONE, 2, 3) || ') ' || SUBSTRING(:CLEANPHONE, 5, 3) || '-' || RIGHT(:CLEANPHONE, 4);
            ELSE
                FORMATTED := :CLEANPHONE;
            END IF;
            RETURN :FORMATTED;
        END LOOP;
    END;
$$;