-- <copyright file="UpdateControlVariable.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2026 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion
--   This procedure provides a reusable way to update variable values in control_variables table
--   Execute this script once before running any orchestration that uses container variable updates
-- ==========================================================================

CREATE OR REPLACE PROCEDURE public.UpdateControlVariable(p_variable_name VARCHAR, p_variable_scope VARCHAR, p_variable_value VARIANT)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
  UPDATE public.control_variables
  SET variable_value = :p_variable_value,
      last_updated_at = CURRENT_TIMESTAMP()
  WHERE variable_name = :p_variable_name
    AND variable_scope = :p_variable_scope;

  RETURN 'Variable updated successfully';
END;
$$;
