-- <copyright file="LoadParameterFile.sql" company="Snowflake Inc">
--        Copyright (c) 2019-2026 Snowflake Inc. All rights reserved.
-- </copyright>

-- ==========================================================================
-- DESCRIPTION:
--   Generated for ETL conversion.
--   Loads variable overrides from a JSON parameter file on a stage and applies
--   them to the row identified by p_target_scope in public.control_variables.
--
--   Cascading scopes (most-specific wins, applied in this order):
--     1. "*global*"                   -> applied to every targeted row
--     2. p_workflow_scope             -> applied when this row's workflow
--                                        section is in the JSON
--     3. p_target_scope (exact)       -> applied to that one row only
--
--   Each step is a separate UPDATE; the last UPDATE that touches a
--   (variable_scope, variable_name) row wins.
--
--   p_workflow_scope is optional (DEFAULT NULL) ONLY for backward compatibility
--   with legacy 2-arg CALL sites that predate the cascade. To exercise the full
--   cascade -- specifically Step 2 (Workflow), which lifts a workflow-section
--   JSON entry into every session under that workflow -- callers MUST pass the
--   workflow's scope as the third argument. Omitting it (or passing NULL)
--   short-circuits Step 2, reducing the procedure to the Global + Exact passes
--   only (the same effective behavior of the pre-cascade procedure for any JSON
--   without a "*global*" key). The converter's emit sites always pass the
--   workflow scope; the DEFAULT NULL is purely a redeploy-safety knob for
--   environments where the new converted output reaches the proc before the
--   matching CALL sites do.
--
--   Expected JSON format:
--     {
--       "*global*":                    { "shared_var":   100 },
--       "WORKFLOWNAME":                { "wf_country":   "Canada", "wf_threshold": 50 },
--       "WORKFLOWNAME.s_m_mapping":    { "m_vacation_bonus": 10 }
--     }
--
--   The "*global*" outer key matches case-insensitively (also "*Global*",
--   "*GLOBAL*"). The asterisks make the sentinel structurally impossible to
--   collide with a real Informatica workflow name (PowerCenter rejects "*"
--   in workflow names), so no workflow can ever be misinterpreted as the
--   cascade marker.
--   Existing per-scope JSONs (only "WF" / "WF.session" keys) continue to work.
--
--   Translating an Informatica .prm parameter-file section header to a JSON
--   outer key:
--     [GLOBAL]                                    -> "*global*"
--     [FOLDER.WF:wkf_name]                        -> "wkf_name"
--     [FOLDER.WF:wkf_name.ST:s_session_name]      -> "wkf_name.s_session_name"
--   Drop the FOLDER prefix and the WF:/ST: tokens; keep the dot between
--   workflow and session.
--
-- Notes on inner-key shape:
--   - Mapping variables use the bare variable name (e.g. "m_vacation_bonus").
--   - Mapplet variables are prefixed with their canonical mapplet name
--     (e.g. "mplt_GET_NEXT_VAL_SEQ_NAME"), since a single mapplet macro is
--     shared across all consumers and the prefix disambiguates per-mapplet
--     state. Per-session isolation is provided by `variable_scope`, not by
--     the variable name.
--   - When a mapping consumes a mapplet through a <SHORTCUT> alias, the
--     canonical mapplet name (NOT the shortcut alias) is what appears in
--     control_variables and dbt_project.yml. Use the canonical key, e.g.
--     "mplt_GET_NEXT_VAL_SEQ_NAME", NOT "Shortcut_to_mplt_GET_NEXT_VAL_SEQ_NAME".
--   - Canonical keys are listed as defaults in the consuming mapping's
--     dbt_project.yml -- copy from there.
-- ==========================================================================

CREATE OR REPLACE PROCEDURE public.LoadParameterFile(
  p_stage_path     VARCHAR,
  p_target_scope   VARCHAR,
  p_workflow_scope VARCHAR DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
    updated_count INTEGER := 0;
BEGIN
    -- If no stage path or scope was provided, nothing to do
    IF (p_stage_path IS NULL OR TRIM(p_stage_path) = '' OR p_target_scope IS NULL OR TRIM(p_target_scope) = '') THEN
        RETURN 0;
    END IF;

    -- Load the JSON file from stage into a temporary table
    CREATE OR REPLACE TEMPORARY TABLE __SNOWCONVERT_LOAD_PARAMETER_FILE_TMP (json_raw VARIANT);

    COPY INTO __SNOWCONVERT_LOAD_PARAMETER_FILE_TMP FROM :p_stage_path
    FILE_FORMAT = (TYPE = JSON);

    -- 1. Global section (least specific, applied first; case-insensitive).
    UPDATE public.control_variables cv
    SET    cv.variable_value  = j.value,
           cv.last_updated_at = CURRENT_TIMESTAMP()
    FROM   __SNOWCONVERT_LOAD_PARAMETER_FILE_TMP t,
           TABLE(FLATTEN(input => t.json_raw))     f1,
           TABLE(FLATTEN(input => f1.value))       j
    WHERE  UPPER(f1.key) = '*GLOBAL*'
      AND  cv.variable_name  = j.key
      AND  cv.variable_scope = :p_target_scope;

    updated_count := updated_count + SQLROWCOUNT;

    -- 2. Workflow section (overrides Global for this scope's workflow parent).
    --    Skipped when target == workflow (i.e., the call is for the WF row itself):
    --    in that case the WF outer key's match is already handled by step 3 (Exact),
    --    so without this guard step 2 would double-apply the same value to the WF row.
    UPDATE public.control_variables cv
    SET    cv.variable_value  = j.value,
           cv.last_updated_at = CURRENT_TIMESTAMP()
    FROM   __SNOWCONVERT_LOAD_PARAMETER_FILE_TMP t,
           TABLE(FLATTEN(input => t.json_raw))     f1,
           TABLE(FLATTEN(input => f1.value))       j
    WHERE  COALESCE(:p_workflow_scope, '') <> ''
      AND  :p_workflow_scope <> :p_target_scope
      AND  f1.key             = :p_workflow_scope
      AND  cv.variable_name  = j.key
      AND  cv.variable_scope = :p_target_scope;

    updated_count := updated_count + SQLROWCOUNT;

    -- 3. Exact section (most specific, applied last; covers WF target and
    --    dotted Session target keys). The session-level JSON outer key uses
    --    a dot ("wfname.sessionname") per the PRM-to-JSON spec, while the
    --    runtime session scope joins with an underscore ("wfname_sessionname"
    --    via GetSessionScope). REPLACE bridges the two; without it, dotted
    --    session keys would never match.
    UPDATE public.control_variables cv
    SET    cv.variable_value  = j.value,
           cv.last_updated_at = CURRENT_TIMESTAMP()
    FROM   __SNOWCONVERT_LOAD_PARAMETER_FILE_TMP t,
           TABLE(FLATTEN(input => t.json_raw))     f1,
           TABLE(FLATTEN(input => f1.value))       j
    WHERE  REPLACE(f1.key, '.', '_') = :p_target_scope
      AND  cv.variable_name  = j.key
      AND  cv.variable_scope = :p_target_scope;

    updated_count := updated_count + SQLROWCOUNT;

    -- Clean up temporary table
    DROP TABLE IF EXISTS __SNOWCONVERT_LOAD_PARAMETER_FILE_TMP;

    RETURN updated_count;
END;
$$;
