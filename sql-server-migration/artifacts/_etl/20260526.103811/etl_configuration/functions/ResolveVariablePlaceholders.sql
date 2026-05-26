-- <copyright file="ResolveVariablePlaceholders.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2026 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion
--   This function resolves {{variable_name}} placeholders in a string
--   by replacing them with variable values from the control_variables table.
--   Used for SQ override JSON where SQL values reference runtime variables.
--   Execute this script once before running any orchestration that uses variable management
-- ==========================================================================

CREATE OR REPLACE FUNCTION public.ResolveVariablePlaceholders(p_text VARCHAR, p_scope VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
  SELECT COALESCE(
    REDUCE(
      ARRAY_AGG(OBJECT_CONSTRUCT('name', variable_name, 'value', variable_value)),
      p_text,
      (acc, var) -> REPLACE(acc, '{{' || var:name::VARCHAR || '}}', COALESCE(var:value::VARCHAR, ''))
    )::VARCHAR,
    p_text
  )
  FROM public.control_variables
  WHERE variable_scope = p_scope
$$;
