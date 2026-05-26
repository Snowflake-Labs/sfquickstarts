-- <copyright file="InitVariablesFromConfig.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2026 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion
--   This procedure loads variable defaults from CONFIG JSON into the control_variables table
--   Only inserts variables that do not already exist (respects persistent values)
--   Execute this script once before running any orchestration that uses variable management
-- ==========================================================================

CREATE OR REPLACE PROCEDURE public.InitVariablesFromConfig(p_variable_scope VARCHAR, p_config_json VARCHAR)
RETURNS INTEGER
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    config_defaults VARIANT;
    variable_scope_count INTEGER := 0;
BEGIN
    config_defaults := PARSE_JSON(:p_config_json);
    
    IF (config_defaults IS NULL) THEN
        RETURN 0;
    END IF;

    INSERT INTO public.control_variables 
        (variable_name, variable_value, variable_type, variable_scope,
         is_parameter, is_persistent, last_updated_at)
    SELECT 
        key,
        value:value,
        value:type::VARCHAR,
        :p_variable_scope,
        COALESCE(value:is_parameter::BOOLEAN, FALSE),
        COALESCE(value:is_persistent::BOOLEAN, FALSE),
        CURRENT_TIMESTAMP()
    FROM TABLE(FLATTEN(input => :config_defaults))
    WHERE NOT EXISTS (
        SELECT 1 FROM public.control_variables
        WHERE variable_name = key
          AND variable_scope = :p_variable_scope
    );

    SELECT COUNT(*) INTO variable_scope_count
    FROM public.control_variables
    WHERE variable_scope = :p_variable_scope;

    RETURN variable_scope_count;
END;
$$;
