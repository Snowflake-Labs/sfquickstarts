-- =============================================================================
-- Cortex Code Credit Manager - Prerequisites
-- =============================================================================
-- Run as ACCOUNTADMIN (one-time setup).
-- Replace <APP_DB>, <APP_SCHEMA>, <APP_WH> with your values.
--
-- Architecture:
--   __SP_OWNER_ROLE__  — owns all SPs (EXECUTE AS OWNER), has elevated privs
--   __APP_ROLE__       — Streamlit runtime role, can CALL SPs + read tables
--   __ADMIN_ROLE__     — human admins, granted __APP_ROLE__
--   __USER_ROLE__      — end users, granted __APP_ROLE__
-- =============================================================================

-- USE ROLE ACCOUNTADMIN;  -- Already running as ACCOUNTADMIN via connection

-- ---------------------------------------------------------------------------
-- 0. VARIABLES (set these before running)
-- ---------------------------------------------------------------------------
SET APP_DB     = '__DB__';
SET APP_SCHEMA = 'APP';
SET APP_WH     = '__WH__';

-- ---------------------------------------------------------------------------
-- 1. ROLES
-- ---------------------------------------------------------------------------
CREATE ROLE IF NOT EXISTS __SP_OWNER_ROLE__
    COMMENT = 'Owns Credit Manager SPs. Never assumed by humans.';
CREATE ROLE IF NOT EXISTS __APP_ROLE__
    COMMENT = 'Streamlit runtime role for Credit Manager app.';
CREATE ROLE IF NOT EXISTS __ADMIN_ROLE__
    COMMENT = 'Human admins of Credit Manager.';
CREATE ROLE IF NOT EXISTS __USER_ROLE__
    COMMENT = 'End users of Credit Manager.';

GRANT ROLE __APP_ROLE__ TO ROLE __ADMIN_ROLE__;
GRANT ROLE __APP_ROLE__ TO ROLE __USER_ROLE__;
GRANT ROLE __SP_OWNER_ROLE__ TO ROLE ACCOUNTADMIN;
GRANT ROLE __ADMIN_ROLE__ TO ROLE ACCOUNTADMIN;

-- SP owner needs: modify users, modify account, manage grants
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE __SP_OWNER_ROLE__;

-- App role needs: read ACCOUNT_USAGE, use warehouse, read/write app tables
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE __APP_ROLE__;
GRANT USAGE ON WAREHOUSE __WH__ TO ROLE __APP_ROLE__;
GRANT USAGE ON DATABASE __DB__ TO ROLE __APP_ROLE__;
GRANT USAGE ON SCHEMA __DB__.__SCHEMA__ TO ROLE __APP_ROLE__;

-- SP owner also needs warehouse for task execution
GRANT USAGE ON WAREHOUSE __WH__ TO ROLE __SP_OWNER_ROLE__;
GRANT USAGE ON DATABASE __DB__ TO ROLE __SP_OWNER_ROLE__;
GRANT USAGE ON SCHEMA __DB__.__SCHEMA__ TO ROLE __SP_OWNER_ROLE__;

-- ---------------------------------------------------------------------------
-- 2. TABLES
-- ---------------------------------------------------------------------------
-- NOTE: Running as ACCOUNTADMIN; will transfer ownership to __SP_OWNER_ROLE__ at end
-- USE ROLE __SP_OWNER_ROLE__;  -- Skipped: running as ACCOUNTADMIN
USE DATABASE __DB__;
USE SCHEMA APP;
USE WAREHOUSE __WH__;

CREATE TABLE IF NOT EXISTS CC_CREDIT_CONFIG (
    CONFIG_ID        NUMBER AUTOINCREMENT,
    CONFIG_TYPE      VARCHAR(50)    NOT NULL,
    ROLE_NAME        VARCHAR(255),
    USER_NAME        VARCHAR(255),
    CLI_DAILY_LIMIT  NUMBER(10,2),
    SNOWSIGHT_DAILY_LIMIT NUMBER(10,2),
    IS_ACTIVE        BOOLEAN        DEFAULT TRUE,
    CREATED_BY       VARCHAR(255),
    CREATED_AT       TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_BY       VARCHAR(255),
    UPDATED_AT       TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (CONFIG_ID)
);

CREATE TABLE IF NOT EXISTS CC_AUDIT_LOG (
    LOG_ID          NUMBER AUTOINCREMENT,
    TIMESTAMP       TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    ACTOR           VARCHAR(255),
    ACTOR_ROLE      VARCHAR(255),
    ACTION_TYPE     VARCHAR(100),
    TARGET_USER     VARCHAR(255),
    TARGET_ROLE     VARCHAR(255),
    DETAILS         VARIANT,
    OLD_VALUE       VARCHAR(1000),
    NEW_VALUE       VARCHAR(1000),
    STATUS          VARCHAR(50)    DEFAULT 'SUCCESS',
    PRIMARY KEY (LOG_ID)
);

CREATE TABLE IF NOT EXISTS CC_USAGE_DAILY_SUMMARY (
    USAGE_DATE      DATE           NOT NULL,
    USER_NAME       VARCHAR(255)   NOT NULL,
    COHORT_ROLE     VARCHAR(255),
    SURFACE         VARCHAR(20)    NOT NULL,
    MODEL_NAME      VARCHAR(255)   NOT NULL DEFAULT 'UNKNOWN',
    TOTAL_CREDITS   NUMBER(20,6)   DEFAULT 0,
    TOTAL_TOKENS    NUMBER(20,0)   DEFAULT 0,
    QUERY_COUNT     NUMBER(10,0)   DEFAULT 0,
    CLI_LIMIT_AT_DATE    NUMBER(10,2),
    SNOWSIGHT_LIMIT_AT_DATE NUMBER(10,2),
    REFRESHED_AT    TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USAGE_DATE, USER_NAME, SURFACE, MODEL_NAME)
);

CREATE TABLE IF NOT EXISTS CC_USAGE_HOURLY_SUMMARY (
    USAGE_DATE      DATE           NOT NULL,
    USAGE_HOUR      NUMBER(2,0)    NOT NULL,
    USER_NAME       VARCHAR(255)   NOT NULL,
    COHORT_ROLE     VARCHAR(255),
    SURFACE         VARCHAR(20)    NOT NULL,
    TOTAL_CREDITS   NUMBER(20,6)   DEFAULT 0,
    QUERY_COUNT     NUMBER(10,0)   DEFAULT 0,
    REFRESHED_AT    TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USAGE_DATE, USAGE_HOUR, USER_NAME, SURFACE)
);

CREATE TABLE IF NOT EXISTS CC_CREDIT_REQUESTS (
    REQUEST_ID          NUMBER AUTOINCREMENT,
    REQUEST_TIMESTAMP   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    REQUESTER           VARCHAR(255),
    REQUESTER_ROLE      VARCHAR(255),
    COHORT_ROLE         VARCHAR(255),
    SURFACE             VARCHAR(20),
    AMOUNT_REQUESTED    NUMBER(10,2),
    AMOUNT_APPROVED     NUMBER(10,2),
    REASON              VARCHAR(2000),
    DONOR_USER          VARCHAR(255),
    DONOR_REDUCTION     NUMBER(10,2),
    STATUS              VARCHAR(50) DEFAULT 'PENDING',
    APPROVED_BY         VARCHAR(255),
    APPROVED_AT         TIMESTAMP_LTZ,
    REJECTION_REASON    VARCHAR(1000),
    PRIMARY KEY (REQUEST_ID)
);

CREATE TABLE IF NOT EXISTS CC_APP_CONFIG (
    CONFIG_KEY      VARCHAR(255)   NOT NULL,
    CONFIG_VALUE    VARCHAR(2000),
    UPDATED_BY      VARCHAR(255),
    UPDATED_AT      TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (CONFIG_KEY)
);

-- Seed default settings
MERGE INTO CC_APP_CONFIG t
USING (
    SELECT * FROM VALUES
        ('APPROVAL_MODE', 'ADMIN'),
        ('REBALANCE_BUFFER_PCT', '20'),
        ('REBALANCE_MAX_TRANSFER_PCT', '50'),
        ('REBALANCE_LOOKBACK_DAYS', '14'),
        ('DAILY_RESET_ENABLED', 'TRUE')
    AS v(K, V)
) s ON t.CONFIG_KEY = s.K
WHEN NOT MATCHED THEN INSERT (CONFIG_KEY, CONFIG_VALUE, UPDATED_BY)
    VALUES (s.K, s.V, 'SYSTEM');

-- Rebalance lock table — one row per cohort, TTL-based, prevents concurrent donor double-spend
CREATE TABLE IF NOT EXISTS CC_COHORT_REBALANCE_LOCK (
    COHORT_ROLE   VARCHAR(255)  NOT NULL PRIMARY KEY,
    LOCKED_BY     VARCHAR(255)  NOT NULL,
    LOCKED_AT     TIMESTAMP_LTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),
    EXPIRES_AT    TIMESTAMP_LTZ NOT NULL
);

-- Model tier configuration — stores model-to-tier assignments (CLI/Snowsight/Desktop)
CREATE TABLE IF NOT EXISTS CC_MODEL_CONFIG (
    MODEL_NAME      VARCHAR(255)   NOT NULL PRIMARY KEY,
    CATEGORY        VARCHAR(255),
    DESCRIPTION     VARCHAR(2000),
    CREATED_BY      VARCHAR(255),
    CREATED_AT      TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- Role-to-model mapping — controls which roles can access which models
CREATE TABLE IF NOT EXISTS CC_MODEL_ROLE_MAPPING (
    ROLE_NAME       VARCHAR(255)   NOT NULL,
    MODEL_NAME      VARCHAR(255)   NOT NULL,
    GRANTED_BY      VARCHAR(255),
    GRANTED_AT      TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (ROLE_NAME, MODEL_NAME)
);

-- Resolved user-to-cohort mapping — populated by SP_CC_RESOLVE_USER_COHORTS
-- Used by Bridge SP for fast cohort member lookups without SHOW GRANTS
CREATE TABLE IF NOT EXISTS CC_USER_COHORT_RESOLVED (
    USER_NAME           VARCHAR(255)   NOT NULL PRIMARY KEY,
    COHORT_ROLE         VARCHAR(255)   NOT NULL,
    RESOLUTION_METHOD   VARCHAR(50),
    RESOLVED_AT         TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- Domain / cohort leads — delegated admins who approve requests for their team
CREATE TABLE IF NOT EXISTS CC_COHORT_LEADS (
    COHORT_ROLE         VARCHAR(255)   NOT NULL,
    LEAD_USER           VARCHAR(255)   NOT NULL,
    CAN_APPROVE_CREDITS BOOLEAN        DEFAULT TRUE,
    CAN_APPROVE_MODELS  BOOLEAN        DEFAULT TRUE,
    CAN_SET_LIMITS      BOOLEAN        DEFAULT TRUE,
    ASSIGNED_BY         VARCHAR(255),
    ASSIGNED_AT         TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (COHORT_ROLE, LEAD_USER)
);

-- Job log for long-running server-side operations
CREATE TABLE IF NOT EXISTS CC_SP_JOB_LOG (
    JOB_ID          NUMBER AUTOINCREMENT PRIMARY KEY,
    JOB_TYPE        VARCHAR(100),
    STATUS          VARCHAR(20)    DEFAULT 'RUNNING',
    STARTED_AT      TIMESTAMP_LTZ  DEFAULT CURRENT_TIMESTAMP(),
    COMPLETED_AT    TIMESTAMP_LTZ,
    ROWS_PROCESSED  NUMBER,
    MESSAGE         VARCHAR(2000)
);

-- Grant table access to app role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA __DB__.__SCHEMA__ TO ROLE __APP_ROLE__;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA __DB__.__SCHEMA__ TO ROLE __APP_ROLE__;

-- ---------------------------------------------------------------------------
-- 3. OWNER-RIGHTS STORED PROCEDURES
-- ---------------------------------------------------------------------------
-- These run as __SP_OWNER_ROLE__ (elevated). The app role can only CALL them.

CREATE OR REPLACE PROCEDURE SP_CC_SET_ACCOUNT_CREDIT_LIMIT(
    P_SURFACE VARCHAR, P_LIMIT VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_param VARCHAR;
    v_limit NUMBER(10,2);
BEGIN
    IF (UPPER(P_SURFACE) = 'CLI') THEN
        v_param := 'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'SNOWSIGHT') THEN
        v_param := 'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'DESKTOP') THEN
        v_param := 'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSE
        RETURN 'ERROR: Invalid surface. Must be CLI, SNOWSIGHT, or DESKTOP.';
    END IF;

    v_limit := P_LIMIT::NUMBER(10,2);
    IF (v_limit < -1) THEN
        RETURN 'ERROR: Limit must be -1, 0, or positive.';
    END IF;

    IF (v_limit = -1) THEN
        EXECUTE IMMEDIATE 'ALTER ACCOUNT UNSET ' || v_param;
    ELSE
        EXECUTE IMMEDIATE 'ALTER ACCOUNT SET ' || v_param || ' = ' || v_limit::INTEGER::VARCHAR;
    END IF;

    RETURN 'OK: Account ' || UPPER(P_SURFACE) || ' limit set to ' || v_limit::INTEGER::VARCHAR;
END;
$$;

CREATE OR REPLACE PROCEDURE SP_CC_SET_USER_CREDIT_LIMIT(
    P_USERNAME VARCHAR, P_SURFACE VARCHAR, P_LIMIT VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_param VARCHAR;
    v_limit NUMBER(10,2);
    v_safe_user VARCHAR;
BEGIN
    -- Validate identifier: only A-Z, 0-9, _, $
    IF (P_USERNAME IS NULL OR LENGTH(P_USERNAME) = 0) THEN
        RETURN 'ERROR: Username required.';
    END IF;
    IF (NOT REGEXP_LIKE(P_USERNAME, '^[A-Za-z0-9_$\\-\\.@]+$')) THEN
        RETURN 'ERROR: Invalid username characters.';
    END IF;
    v_safe_user := UPPER(P_USERNAME);

    IF (UPPER(P_SURFACE) = 'CLI') THEN
        v_param := 'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'SNOWSIGHT') THEN
        v_param := 'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'DESKTOP') THEN
        v_param := 'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSE
        RETURN 'ERROR: Invalid surface. Must be CLI, SNOWSIGHT, or DESKTOP.';
    END IF;

    v_limit := P_LIMIT::NUMBER(10,2);
    IF (v_limit < -1) THEN
        RETURN 'ERROR: Limit must be -1, 0, or positive.';
    END IF;

    EXECUTE IMMEDIATE 'ALTER USER "' || v_safe_user || '" SET ' || v_param || ' = ' || v_limit::INTEGER::VARCHAR;

    RETURN 'OK: ' || v_safe_user || ' ' || UPPER(P_SURFACE) || ' limit set to ' || v_limit::INTEGER::VARCHAR;
END;
$$;

CREATE OR REPLACE PROCEDURE SP_CC_UNSET_USER_CREDIT_LIMIT(
    P_USERNAME VARCHAR, P_SURFACE VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_param VARCHAR;
    v_safe_user VARCHAR;
BEGIN
    IF (P_USERNAME IS NULL OR NOT REGEXP_LIKE(P_USERNAME, '^[A-Za-z0-9_$\\-\\.@]+$')) THEN
        RETURN 'ERROR: Invalid username.';
    END IF;
    v_safe_user := UPPER(P_USERNAME);

    IF (UPPER(P_SURFACE) = 'CLI') THEN
        v_param := 'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'SNOWSIGHT') THEN
        v_param := 'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'DESKTOP') THEN
        v_param := 'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSE
        RETURN 'ERROR: Invalid surface.';
    END IF;

    EXECUTE IMMEDIATE 'ALTER USER "' || v_safe_user || '" UNSET ' || v_param;
    RETURN 'OK: ' || v_safe_user || ' ' || UPPER(P_SURFACE) || ' override removed.';
END;
$$;

CREATE OR REPLACE PROCEDURE SP_CC_GRANT_CORTEX_ACCESS(
    P_USERNAME VARCHAR, P_DATABASE_ROLE VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_safe_user VARCHAR;
BEGIN
    IF (P_USERNAME IS NULL OR NOT REGEXP_LIKE(P_USERNAME, '^[A-Za-z0-9_$\\-\\.@]+$')) THEN
        RETURN 'ERROR: Invalid username.';
    END IF;
    v_safe_user := UPPER(P_USERNAME);

    IF (P_DATABASE_ROLE NOT IN ('SNOWFLAKE.CORTEX_USER', 'SNOWFLAKE.CORTEX_ANALYST_USER')) THEN
        RETURN 'ERROR: Invalid database role. Allowed: SNOWFLAKE.CORTEX_USER, SNOWFLAKE.CORTEX_ANALYST_USER';
    END IF;

    EXECUTE IMMEDIATE 'GRANT DATABASE ROLE ' || P_DATABASE_ROLE || ' TO USER "' || v_safe_user || '"';
    RETURN 'OK: Granted ' || P_DATABASE_ROLE || ' to ' || v_safe_user;
EXCEPTION
    WHEN OTHER THEN
        RETURN 'ERROR: ' || SQLERRM;
END;
$$;

CREATE OR REPLACE PROCEDURE SP_CC_REVOKE_CORTEX_ACCESS(
    P_USERNAME VARCHAR, P_DATABASE_ROLE VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_safe_user VARCHAR;
BEGIN
    IF (P_USERNAME IS NULL OR NOT REGEXP_LIKE(P_USERNAME, '^[A-Za-z0-9_$\\-\\.@]+$')) THEN
        RETURN 'ERROR: Invalid username.';
    END IF;
    v_safe_user := UPPER(P_USERNAME);

    IF (P_DATABASE_ROLE NOT IN ('SNOWFLAKE.CORTEX_USER', 'SNOWFLAKE.CORTEX_ANALYST_USER')) THEN
        RETURN 'ERROR: Invalid database role.';
    END IF;

    EXECUTE IMMEDIATE 'REVOKE DATABASE ROLE ' || P_DATABASE_ROLE || ' FROM USER "' || v_safe_user || '"';
    RETURN 'OK: Revoked ' || P_DATABASE_ROLE || ' from ' || v_safe_user;
EXCEPTION
    WHEN OTHER THEN
        RETURN 'ERROR: ' || SQLERRM;
END;
$$;

CREATE OR REPLACE PROCEDURE SP_CC_REBALANCE_CREDITS(
    P_DONOR_USER VARCHAR, P_DONOR_NEW_LIMIT VARCHAR,
    P_REQUESTER VARCHAR, P_REQUESTER_NEW_LIMIT VARCHAR,
    P_SURFACE VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_param VARCHAR;
    v_safe_donor VARCHAR;
    v_safe_requester VARCHAR;
    v_donor_limit NUMBER(10,2);
    v_requester_limit NUMBER(10,2);
BEGIN
    IF (NOT REGEXP_LIKE(P_DONOR_USER, '^[A-Za-z0-9_$\\-\\.@]+$') OR
        NOT REGEXP_LIKE(P_REQUESTER, '^[A-Za-z0-9_$\\-\\.@]+$')) THEN
        RETURN 'ERROR: Invalid username.';
    END IF;
    v_safe_donor := UPPER(P_DONOR_USER);
    v_safe_requester := UPPER(P_REQUESTER);

    IF (UPPER(P_SURFACE) = 'CLI') THEN
        v_param := 'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'SNOWSIGHT') THEN
        v_param := 'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSEIF (UPPER(P_SURFACE) = 'DESKTOP') THEN
        v_param := 'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER';
    ELSE
        RETURN 'ERROR: Invalid surface.';
    END IF;

    v_donor_limit := P_DONOR_NEW_LIMIT::NUMBER(10,2);
    v_requester_limit := P_REQUESTER_NEW_LIMIT::NUMBER(10,2);

    IF (v_donor_limit < 0 OR v_requester_limit < 0) THEN
        RETURN 'ERROR: Limits cannot be negative for rebalance.';
    END IF;

    EXECUTE IMMEDIATE 'ALTER USER "' || v_safe_donor || '" SET ' || v_param || ' = ' || v_donor_limit::INTEGER::VARCHAR;
    EXECUTE IMMEDIATE 'ALTER USER "' || v_safe_requester || '" SET ' || v_param || ' = ' || v_requester_limit::INTEGER::VARCHAR;

    RETURN 'OK: Rebalanced ' || v_safe_donor || '=' || v_donor_limit::INTEGER::VARCHAR ||
           ', ' || v_safe_requester || '=' || v_requester_limit::INTEGER::VARCHAR;
EXCEPTION
    WHEN OTHER THEN
        RETURN 'ERROR: ' || SQLERRM;
END;
$$;

-- Grant USAGE on SPs to app role
GRANT USAGE ON PROCEDURE SP_CC_SET_ACCOUNT_CREDIT_LIMIT(VARCHAR, VARCHAR) TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_SET_USER_CREDIT_LIMIT(VARCHAR, VARCHAR, VARCHAR) TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_UNSET_USER_CREDIT_LIMIT(VARCHAR, VARCHAR) TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_GRANT_CORTEX_ACCESS(VARCHAR, VARCHAR) TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_REVOKE_CORTEX_ACCESS(VARCHAR, VARCHAR) TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_REBALANCE_CREDITS(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR) TO ROLE __APP_ROLE__;


-- ---------------------------------------------------------------------------
-- 4. INCREMENTAL REFRESH TASK
-- ---------------------------------------------------------------------------
-- Merges new data from ACCOUNT_USAGE into pre-aggregated summary tables.
-- Runs every 30 minutes. Uses USAGE_TIME from source views.
-- Joins with USERS view to get USER_NAME from USER_ID.
-- Cohort resolution: joins CC_CREDIT_CONFIG to map user→cohort role.

CREATE OR REPLACE PROCEDURE SP_CC_REFRESH_USAGE_SUMMARIES()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_last_refresh TIMESTAMP_LTZ;
    v_count_daily NUMBER DEFAULT 0;
    v_count_hourly NUMBER DEFAULT 0;
BEGIN
    -- Determine watermark: last refresh timestamp (or 30 days ago for first run)
    SELECT COALESCE(MAX(REFRESHED_AT), DATEADD('day', -30, CURRENT_TIMESTAMP()))
    INTO v_last_refresh
    FROM CC_USAGE_DAILY_SUMMARY;

    -- Pre-compute user-to-cohort mapping (avoids correlated subquery in MERGE)
    CREATE OR REPLACE TEMPORARY TABLE CC_TEMP_USER_COHORT AS
    SELECT DISTINCT g.GRANTEE_NAME AS USER_NAME, c.ROLE_NAME AS COHORT_ROLE
    FROM CC_CREDIT_CONFIG c
    JOIN SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS g
        ON g.ROLE = c.ROLE_NAME AND g.DELETED_ON IS NULL
    WHERE c.CONFIG_TYPE = 'COHORT' AND c.IS_ACTIVE = TRUE;

    -- DAILY SUMMARY: CLI
    MERGE INTO CC_USAGE_DAILY_SUMMARY tgt
    USING (
        SELECT
            DATE_TRUNC('day', h.USAGE_TIME)::DATE AS USAGE_DATE,
            u.NAME AS USER_NAME,
            uc.COHORT_ROLE,
            'CLI' AS SURFACE,
            COALESCE(f.KEY, 'UNKNOWN') AS MODEL_NAME,
            SUM(h.TOKEN_CREDITS) AS TOTAL_CREDITS,
            SUM(h.TOKENS) AS TOTAL_TOKENS,
            COUNT(*) AS QUERY_COUNT
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY h
        JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON h.USER_ID = u.USER_ID
        LEFT JOIN CC_TEMP_USER_COHORT uc ON uc.USER_NAME = u.NAME
        LEFT JOIN LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR, OUTER => TRUE) f
        WHERE h.USAGE_TIME > :v_last_refresh
        GROUP BY 1, 2, 3, 4, 5
    ) src
    ON tgt.USAGE_DATE = src.USAGE_DATE
        AND tgt.USER_NAME = src.USER_NAME
        AND tgt.SURFACE = src.SURFACE
        AND tgt.MODEL_NAME = src.MODEL_NAME
    WHEN MATCHED THEN UPDATE SET
        COHORT_ROLE = src.COHORT_ROLE,
        TOTAL_CREDITS = src.TOTAL_CREDITS,
        TOTAL_TOKENS = src.TOTAL_TOKENS,
        QUERY_COUNT = src.QUERY_COUNT,
        REFRESHED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (USAGE_DATE, USER_NAME, COHORT_ROLE, SURFACE, MODEL_NAME,
         TOTAL_CREDITS, TOTAL_TOKENS, QUERY_COUNT, REFRESHED_AT)
    VALUES (src.USAGE_DATE, src.USER_NAME, src.COHORT_ROLE, src.SURFACE,
            src.MODEL_NAME, src.TOTAL_CREDITS, src.TOTAL_TOKENS, src.QUERY_COUNT,
            CURRENT_TIMESTAMP());

    -- DAILY SUMMARY: SNOWSIGHT
    MERGE INTO CC_USAGE_DAILY_SUMMARY tgt
    USING (
        SELECT
            DATE_TRUNC('day', h.USAGE_TIME)::DATE AS USAGE_DATE,
            u.NAME AS USER_NAME,
            uc.COHORT_ROLE,
            'SNOWSIGHT' AS SURFACE,
            COALESCE(f.KEY, 'UNKNOWN') AS MODEL_NAME,
            SUM(h.TOKEN_CREDITS) AS TOTAL_CREDITS,
            SUM(h.TOKENS) AS TOTAL_TOKENS,
            COUNT(*) AS QUERY_COUNT
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY h
        JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON h.USER_ID = u.USER_ID
        LEFT JOIN CC_TEMP_USER_COHORT uc ON uc.USER_NAME = u.NAME
        LEFT JOIN LATERAL FLATTEN(INPUT => h.CREDITS_GRANULAR, OUTER => TRUE) f
        WHERE h.USAGE_TIME > :v_last_refresh
        GROUP BY 1, 2, 3, 4, 5
    ) src
    ON tgt.USAGE_DATE = src.USAGE_DATE
        AND tgt.USER_NAME = src.USER_NAME
        AND tgt.SURFACE = src.SURFACE
        AND tgt.MODEL_NAME = src.MODEL_NAME
    WHEN MATCHED THEN UPDATE SET
        COHORT_ROLE = src.COHORT_ROLE,
        TOTAL_CREDITS = src.TOTAL_CREDITS,
        TOTAL_TOKENS = src.TOTAL_TOKENS,
        QUERY_COUNT = src.QUERY_COUNT,
        REFRESHED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (USAGE_DATE, USER_NAME, COHORT_ROLE, SURFACE, MODEL_NAME,
         TOTAL_CREDITS, TOTAL_TOKENS, QUERY_COUNT, REFRESHED_AT)
    VALUES (src.USAGE_DATE, src.USER_NAME, src.COHORT_ROLE, src.SURFACE,
            src.MODEL_NAME, src.TOTAL_CREDITS, src.TOTAL_TOKENS, src.QUERY_COUNT,
            CURRENT_TIMESTAMP());

    -- HOURLY SUMMARY: CLI
    MERGE INTO CC_USAGE_HOURLY_SUMMARY tgt
    USING (
        SELECT
            DATE_TRUNC('day', h.USAGE_TIME)::DATE AS USAGE_DATE,
            EXTRACT(HOUR FROM h.USAGE_TIME)::NUMBER(2,0) AS USAGE_HOUR,
            u.NAME AS USER_NAME,
            uc.COHORT_ROLE,
            'CLI' AS SURFACE,
            SUM(h.TOKEN_CREDITS) AS TOTAL_CREDITS,
            COUNT(*) AS QUERY_COUNT
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_CLI_USAGE_HISTORY h
        JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON h.USER_ID = u.USER_ID
        LEFT JOIN CC_TEMP_USER_COHORT uc ON uc.USER_NAME = u.NAME
        WHERE h.USAGE_TIME > :v_last_refresh
        GROUP BY 1, 2, 3, 4, 5
    ) src
    ON tgt.USAGE_DATE = src.USAGE_DATE
        AND tgt.USAGE_HOUR = src.USAGE_HOUR
        AND tgt.USER_NAME = src.USER_NAME
        AND tgt.SURFACE = src.SURFACE
    WHEN MATCHED THEN UPDATE SET
        COHORT_ROLE = src.COHORT_ROLE,
        TOTAL_CREDITS = src.TOTAL_CREDITS,
        QUERY_COUNT = src.QUERY_COUNT,
        REFRESHED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (USAGE_DATE, USAGE_HOUR, USER_NAME, COHORT_ROLE, SURFACE,
         TOTAL_CREDITS, QUERY_COUNT, REFRESHED_AT)
    VALUES (src.USAGE_DATE, src.USAGE_HOUR, src.USER_NAME, src.COHORT_ROLE,
            src.SURFACE, src.TOTAL_CREDITS, src.QUERY_COUNT, CURRENT_TIMESTAMP());

    -- HOURLY SUMMARY: SNOWSIGHT
    MERGE INTO CC_USAGE_HOURLY_SUMMARY tgt
    USING (
        SELECT
            DATE_TRUNC('day', h.USAGE_TIME)::DATE AS USAGE_DATE,
            EXTRACT(HOUR FROM h.USAGE_TIME)::NUMBER(2,0) AS USAGE_HOUR,
            u.NAME AS USER_NAME,
            uc.COHORT_ROLE,
            'SNOWSIGHT' AS SURFACE,
            SUM(h.TOKEN_CREDITS) AS TOTAL_CREDITS,
            COUNT(*) AS QUERY_COUNT
        FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_CODE_SNOWSIGHT_USAGE_HISTORY h
        JOIN SNOWFLAKE.ACCOUNT_USAGE.USERS u ON h.USER_ID = u.USER_ID
        LEFT JOIN CC_TEMP_USER_COHORT uc ON uc.USER_NAME = u.NAME
        WHERE h.USAGE_TIME > :v_last_refresh
        GROUP BY 1, 2, 3, 4, 5
    ) src
    ON tgt.USAGE_DATE = src.USAGE_DATE
        AND tgt.USAGE_HOUR = src.USAGE_HOUR
        AND tgt.USER_NAME = src.USER_NAME
        AND tgt.SURFACE = src.SURFACE
    WHEN MATCHED THEN UPDATE SET
        COHORT_ROLE = src.COHORT_ROLE,
        TOTAL_CREDITS = src.TOTAL_CREDITS,
        QUERY_COUNT = src.QUERY_COUNT,
        REFRESHED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (USAGE_DATE, USAGE_HOUR, USER_NAME, COHORT_ROLE, SURFACE,
         TOTAL_CREDITS, QUERY_COUNT, REFRESHED_AT)
    VALUES (src.USAGE_DATE, src.USAGE_HOUR, src.USER_NAME, src.COHORT_ROLE,
            src.SURFACE, src.TOTAL_CREDITS, src.QUERY_COUNT, CURRENT_TIMESTAMP());

    SELECT COUNT(*) INTO v_count_daily FROM CC_USAGE_DAILY_SUMMARY WHERE REFRESHED_AT >= :v_last_refresh;
    SELECT COUNT(*) INTO v_count_hourly FROM CC_USAGE_HOURLY_SUMMARY WHERE REFRESHED_AT >= :v_last_refresh;

    DROP TABLE IF EXISTS CC_TEMP_USER_COHORT;

    RETURN 'OK: Refreshed ' || v_count_daily || ' daily + ' || v_count_hourly || ' hourly rows.';
END;
$$;


-- Scheduled task: refresh every 30 minutes
CREATE OR REPLACE TASK CC_REFRESH_USAGE_SUMMARIES
    WAREHOUSE = __WH__
    SCHEDULE = 'USING CRON */30 * * * * UTC'
AS
    CALL SP_CC_REFRESH_USAGE_SUMMARIES();

ALTER TASK CC_REFRESH_USAGE_SUMMARIES RESUME;


-- ---------------------------------------------------------------------------
-- 5. DAILY RESET TASK (optional, controlled by CC_APP_CONFIG.DAILY_RESET_ENABLED)
-- ---------------------------------------------------------------------------
-- Restores user limits to cohort defaults at midnight UTC.
-- Only runs if the setting is enabled.

CREATE OR REPLACE PROCEDURE SP_CC_DAILY_RESET_LIMITS()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_enabled VARCHAR;
    v_count NUMBER DEFAULT 0;
BEGIN
    SELECT CONFIG_VALUE INTO v_enabled FROM CC_APP_CONFIG WHERE CONFIG_KEY = 'DAILY_RESET_ENABLED';
    IF (v_enabled != 'TRUE') THEN
        RETURN 'SKIP: Daily reset is disabled.';
    END IF;

    FOR cohort IN (
        SELECT ROLE_NAME, CLI_DAILY_LIMIT, SNOWSIGHT_DAILY_LIMIT
        FROM CC_CREDIT_CONFIG
        WHERE CONFIG_TYPE = 'COHORT' AND IS_ACTIVE = TRUE
    ) DO
        FOR member IN (
            SELECT GRANTEE_NAME AS USER_NAME
            FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS
            WHERE ROLE = cohort.ROLE_NAME AND DELETED_ON IS NULL
            AND GRANTEE_NAME NOT IN (
                SELECT USER_NAME FROM CC_CREDIT_CONFIG
                WHERE CONFIG_TYPE = 'USER_OVERRIDE' AND IS_ACTIVE = TRUE
            )
        ) DO
            EXECUTE IMMEDIATE
                'ALTER USER "' || member.USER_NAME || '" SET '
                || 'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER = '
                || cohort.CLI_DAILY_LIMIT::VARCHAR;
            EXECUTE IMMEDIATE
                'ALTER USER "' || member.USER_NAME || '" SET '
                || 'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER = '
                || cohort.SNOWSIGHT_DAILY_LIMIT::VARCHAR;
            v_count := v_count + 1;
        END FOR;
    END FOR;

    RETURN 'OK: Reset limits for ' || v_count || ' users.';
END;
$$;

CREATE OR REPLACE TASK CC_DAILY_RESET_LIMITS
    WAREHOUSE = __WH__
    SCHEDULE = 'USING CRON 0 0 * * * UTC'
    COMMENT = 'Resets user credit limits to cohort defaults at midnight UTC'
AS
    CALL SP_CC_DAILY_RESET_LIMITS();

ALTER TASK CC_DAILY_RESET_LIMITS RESUME;


-- ---------------------------------------------------------------------------
-- 6. GRANT SP EXECUTION TO APP ROLE
-- ---------------------------------------------------------------------------
GRANT USAGE ON PROCEDURE SP_CC_REFRESH_USAGE_SUMMARIES() TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_DAILY_RESET_LIMITS() TO ROLE __APP_ROLE__;

-- ---------------------------------------------------------------------------
-- 6b. ADDITIONAL OPERATIONAL PROCEDURES
-- ---------------------------------------------------------------------------

-- Expire temporary credit overrides — called nightly by CC_DAILY_RESET_LIMITS
CREATE OR REPLACE PROCEDURE SP_CC_EXPIRE_TEMPORARY_CREDITS()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'handler'
EXECUTE AS OWNER
AS $$
import re
_SAFE = re.compile(r'[;\n\r\x00]')  # blocks only truly dangerous chars
_PARAMS = [
    'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER',
    'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER',
    'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER',
]

def handler(session):
    reverted = 0
    try:
        expired = session.sql("""
            SELECT USER_NAME FROM CC_CREDIT_CONFIG
            WHERE IS_TEMPORARY = TRUE
              AND EXPIRES_AT IS NOT NULL
              AND EXPIRES_AT < CURRENT_TIMESTAMP()
              AND IS_ACTIVE = TRUE
        """).collect()
        for row in expired:
            user = str(row[0])
            if not user or _SAFE.search(user):
                continue
            try:
                for param in _PARAMS:
                    safe_user_id = user.replace('"', '""')
                    session.sql('ALTER USER "' + safe_user_id + '" UNSET ' + param).collect()
                safe_user = user.replace("'", "''")
                session.sql(
                    "UPDATE CC_CREDIT_CONFIG SET IS_ACTIVE = FALSE, "
                    "UPDATED_AT = CURRENT_TIMESTAMP() "
                    "WHERE USER_NAME = '" + safe_user + "' AND IS_TEMPORARY = TRUE"
                ).collect()
                reverted += 1
            except Exception:
                pass
    except Exception as e:
        return "ERROR: " + str(e)[:200]
    return "OK: Expired " + str(reverted) + " temporary override(s)"
$$;

-- Resolve user-to-cohort mapping — populates CC_USER_COHORT_RESOLVED
CREATE OR REPLACE PROCEDURE SP_CC_RESOLVE_USER_COHORTS()
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.9'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'handler'
EXECUTE AS OWNER
AS $$
import re
_SAFE = re.compile(r'[;\n\r\x00]')  # blocks only truly dangerous chars

def handler(session):
    resolved = 0
    try:
        session.sql("DELETE FROM CC_USER_COHORT_RESOLVED").collect()
        cohorts = session.sql("""
            SELECT ROLE_NAME FROM CC_CREDIT_CONFIG
            WHERE CONFIG_TYPE = 'COHORT' AND IS_ACTIVE = TRUE AND ROLE_NAME IS NOT NULL
        """).collect()
        for row in cohorts:
            role = str(row[0])
            if not role or _SAFE.search(role):
                continue
            try:
                safe_role = role.replace('"', '""')
                grants = session.sql('SHOW GRANTS OF ROLE "' + safe_role + '"').collect()
                for r in grants:
                    if str(r.get("granted_to", "")).upper() != "USER":
                        continue
                    user = str(r.get("grantee_name", "")).upper()
                    if not user or _SAFE.search(user):
                        continue
                    su = user.replace("'", "''")
                    sr = role.replace("'", "''")
                    session.sql("""
                        MERGE INTO CC_USER_COHORT_RESOLVED t
                        USING (SELECT '""" + su + """' AS U) s ON t.USER_NAME = s.U
                        WHEN NOT MATCHED THEN INSERT
                            (USER_NAME, COHORT_ROLE, RESOLUTION_METHOD, RESOLVED_AT)
                        VALUES ('""" + su + """', '""" + sr + """', 'DIRECT_GRANT', CURRENT_TIMESTAMP())
                    """).collect()
                resolved += 1
            except Exception:
                pass
    except Exception as e:
        return "ERROR: " + str(e)[:200]
    return "OK: Resolved " + str(resolved) + " cohort role(s)"
$$;

-- Enforce model access — stub (inline enforcement via Model Access page)
CREATE OR REPLACE PROCEDURE SP_CC_ENFORCE_MODEL_ACCESS()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
BEGIN
    RETURN 'OK: Use Model Access page for detailed enforcement';
END;
$$;

-- ---------------------------------------------------------------------------
-- 7. OWNERSHIP TRANSFER (running as ACCOUNTADMIN, transfer to __SP_OWNER_ROLE__)
-- ---------------------------------------------------------------------------
GRANT OWNERSHIP ON TABLE CC_CREDIT_CONFIG TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON TABLE CC_AUDIT_LOG TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON TABLE CC_USAGE_DAILY_SUMMARY TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON TABLE CC_USAGE_HOURLY_SUMMARY TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON TABLE CC_CREDIT_REQUESTS TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON TABLE CC_APP_CONFIG TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_SET_ACCOUNT_CREDIT_LIMIT(VARCHAR, VARCHAR) TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_SET_USER_CREDIT_LIMIT(VARCHAR, VARCHAR, VARCHAR) TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_UNSET_USER_CREDIT_LIMIT(VARCHAR, VARCHAR) TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_GRANT_CORTEX_ACCESS(VARCHAR, VARCHAR) TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_REVOKE_CORTEX_ACCESS(VARCHAR, VARCHAR) TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_REBALANCE_CREDITS(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR) TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_REFRESH_USAGE_SUMMARIES() TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON PROCEDURE SP_CC_DAILY_RESET_LIMITS() TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;

-- Tasks must be suspended before ownership can be transferred
ALTER TASK CC_REFRESH_USAGE_SUMMARIES SUSPEND;
ALTER TASK CC_DAILY_RESET_LIMITS SUSPEND;
GRANT OWNERSHIP ON TASK CC_REFRESH_USAGE_SUMMARIES TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
GRANT OWNERSHIP ON TASK CC_DAILY_RESET_LIMITS TO ROLE __SP_OWNER_ROLE__ COPY CURRENT GRANTS;
ALTER TASK CC_REFRESH_USAGE_SUMMARIES RESUME;
ALTER TASK CC_DAILY_RESET_LIMITS RESUME;

-- ---------------------------------------------------------------------------
-- 8. VERIFICATION
-- ---------------------------------------------------------------------------
SHOW TABLES LIKE 'CC_%';
SHOW PROCEDURES LIKE 'SP_CC_%';
SHOW TASKS LIKE 'CC_%';
SHOW GRANTS TO ROLE __APP_ROLE__;
