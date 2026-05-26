-- <copyright file="GetControlVariableUDF.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2025 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion
--   This function provides a reusable way to retrieve variable values from control_variables table
--   Execute this script once before running any orchestration that uses container variable declarations
-- ==========================================================================

CREATE OR REPLACE FUNCTION public.GetControlVariableUDF(p_variable_name VARCHAR, p_variable_scope VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
AS
$$
  SELECT variable_value
  FROM public.control_variables
  WHERE variable_name = p_variable_name
    AND variable_scope = p_variable_scope
  LIMIT 1
$$;