-- <copyright file="ApplyInheritedVariables.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2026 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion
--   This procedure applies inherited variables passed from a parent package
--   to a child stored procedure. It updates existing variables in the
--   control_variables table with values from the JSON parameter.
--   Execute this script once before running any orchestration that uses
--   Execute Package Task parameter bindings.
-- ==========================================================================

CREATE OR REPLACE PROCEDURE public.ApplyInheritedVariables(
  p_variable_scope VARCHAR,
  p_inherited_vars_json VARCHAR
)
RETURNS INTEGER
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  inherited_vars VARIANT;
  updated_count INTEGER := 0;
BEGIN
  -- If no inherited variables were passed, nothing to do
  IF (p_inherited_vars_json IS NULL OR p_inherited_vars_json = '') THEN
    RETURN 0;
  END IF;

  -- Parse the JSON containing inherited variable values
  inherited_vars := PARSE_JSON(:p_inherited_vars_json);

  IF (inherited_vars IS NULL) THEN
    RETURN 0;
  END IF;

  -- Update existing variables with inherited values from parent
  -- JSON structure: {"VarName": <value>, ...}
  UPDATE public.control_variables cv
  SET variable_value = f.value,
      last_updated_at = CURRENT_TIMESTAMP()
  FROM TABLE(FLATTEN(input => :inherited_vars)) f
  WHERE cv.variable_name = f.key
    AND cv.variable_scope = :p_variable_scope;

  updated_count := SQLROWCOUNT;
  RETURN updated_count;
END;
$$;
