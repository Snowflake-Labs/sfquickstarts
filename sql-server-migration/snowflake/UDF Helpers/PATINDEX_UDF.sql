-- <copyright file="PATINDEX_UDF.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2025 Snowflake Inc. All rights reserved.
-- </copyright>

-- =========================================================================================================
-- Description: The PATINDEX_UDF function returns the starting position of the first occurrence of a pattern 
-- in a specified expression or zeros if the pattern is not found
-- =========================================================================================================

CREATE OR REPLACE FUNCTION PUBLIC.PATINDEX_UDF(PATTERN VARCHAR, EXPRESSION VARCHAR)
RETURNS INTEGER
LANGUAGE SQL
IMMUTABLE
COMMENT = '{ "origin": "sf_sc", "name": "snowconvert", "version": {  "major": 2,  "minor": 29,  "patch": "0-Pr.424" }, "attributes": {  "component": "udf",  "convertedOn": "05/26/2026",  "domain": "no-domain-provided",  "migrationid": "JmWeAWK07nK+5zZKD9nimA==" }}'
AS
$$
   REGEXP_INSTR(EXPRESSION, REPLACE(REPLACE(PATTERN, '%'), '_', '\.*'))
$$;