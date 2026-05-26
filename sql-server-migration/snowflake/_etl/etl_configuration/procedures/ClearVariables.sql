-- <copyright file="ClearVariables.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2026 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion
--   This procedure deletes non-persistent variables for a scope, preserving persistent values
--   Execute this script once before running any orchestration that uses variable management
-- ==========================================================================

CREATE OR REPLACE PROCEDURE public.ClearVariables(p_variable_scope VARCHAR)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
    DELETE FROM public.control_variables
    WHERE variable_scope = :p_variable_scope
      AND is_persistent = FALSE;
    
    RETURN 'Cleared non-persistent variables for scope: ' || :p_variable_scope;
END;
$$;
