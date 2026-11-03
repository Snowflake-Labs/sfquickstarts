-- ===========================================================================
-- CoCo Control Hub — Chargeback Tier 1 (warehouse-credit attribution)
-- ===========================================================================
-- Adds the *missing* half of CoCo cost: the WAREHOUSE / SQL compute credits that
-- Cortex Code burns running queries on a user's behalf (LLM token credits are
-- already covered by CC_USAGE_DAILY_SUMMARY). Plus a trimmed, confidence-labeled
-- waterfall that attributes usage to a billing entity, and an unattributed queue.
--
-- Design (see coco-hub-integration-analysis memory):
--   * Heavy ACCOUNT_USAGE scans run ONCE/day into small CC_* summary tables via a
--     scheduled task (same pattern as CC_REFRESH_USAGE_SUMMARIES). Pages read the
--     summaries → fast. Raw QUERY_HISTORY / QUERY_ATTRIBUTION_HISTORY are never
--     queried on page load (the per-user drill-down is a scoped live query).
--   * CoCo auto-stamps query_tag:app = cortex_code_cli / _desktop / _snowsight /
--     _sandbox / _api → this both identifies CoCo SQL and encodes the surface.
--   * QUERY_ATTRIBUTION_HISTORY.credits_attributed_compute = warehouse credits.
--   * Attribution is at the USER x DAY x SURFACE grain (NOT per-event): CoCo
--     neuters per-query tags, so L3/L4/L5 resolve per-user anyway — a per-event
--     fact would add cost for no signal.
--
-- Placeholders (__DB__, __SCHEMA__, __WH__, __APP_ROLE__) match prerequisites.sql
-- and are substituted at setup time. SPs run EXECUTE AS OWNER (owner has
-- IMPORTED PRIVILEGES on SNOWFLAKE for ACCOUNT_USAGE access).
-- ===========================================================================

USE DATABASE __DB__;
USE SCHEMA __SCHEMA__;
USE WAREHOUSE __WH__;

-- ---------------------------------------------------------------------------
-- 1. TABLES
-- ---------------------------------------------------------------------------

-- Daily rollup of CoCo warehouse/compute credits per user x surface.
-- Populated by SP_CC_REFRESH_WAREHOUSE_USAGE (trailing-window MERGE).
CREATE TABLE IF NOT EXISTS CC_WAREHOUSE_USAGE_DAILY (
    USAGE_DATE        DATE          NOT NULL,
    USER_NAME         VARCHAR(255)  NOT NULL,
    SURFACE           VARCHAR(20)   NOT NULL,           -- CLI/DESKTOP/SNOWSIGHT/SANDBOX/API/OTHER
    QUERY_COUNT       NUMBER(18,0)  DEFAULT 0,
    WAREHOUSE_CREDITS NUMBER(20,6)  DEFAULT 0,
    REFRESHED_AT      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USAGE_DATE, USER_NAME, SURFACE)
);

-- L3 — exact service-account → billing entity (highest confidence).
CREATE TABLE IF NOT EXISTS CC_SERVICE_USER_MAPPING (
    USER_NAME    VARCHAR(255) NOT NULL PRIMARY KEY,
    ENTITY       VARCHAR(255) NOT NULL,                 -- customer / partner / project label
    ENTITY_TYPE  VARCHAR(50)  DEFAULT 'CUSTOMER',       -- CUSTOMER / PARTNER / PROJECT
    UPDATED_BY   VARCHAR(255),
    UPDATED_AT   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- L5 — role → billing entity (medium confidence).
CREATE TABLE IF NOT EXISTS CC_ROLE_MAPPING (
    ROLE_NAME    VARCHAR(255) NOT NULL PRIMARY KEY,
    ENTITY       VARCHAR(255) NOT NULL,
    ENTITY_TYPE  VARCHAR(50)  DEFAULT 'CUSTOMER',
    UPDATED_BY   VARCHAR(255),
    UPDATED_AT   TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Output of the waterfall: one row per user x day x surface, entity + confidence.
CREATE TABLE IF NOT EXISTS CC_ATTRIBUTION_DAILY (
    USAGE_DATE        DATE          NOT NULL,
    USER_NAME         VARCHAR(255)  NOT NULL,
    SURFACE           VARCHAR(20)   NOT NULL,
    ENTITY            VARCHAR(255),                      -- NULL when UNATTRIBUTED
    ENTITY_TYPE       VARCHAR(50),
    ATTR_METHOD       VARCHAR(40)   NOT NULL,            -- L3_SERVICE_USER/L4_USER_TAG/L5_ROLE/UNATTRIBUTED
    CONFIDENCE        VARCHAR(10)   NOT NULL,            -- HIGH/MEDIUM/NONE
    TOKEN_CREDITS     NUMBER(20,6)  DEFAULT 0,
    WAREHOUSE_CREDITS NUMBER(20,6)  DEFAULT 0,
    REFRESHED_AT      TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (USAGE_DATE, USER_NAME, SURFACE)
);

-- Actionable queue for usage the waterfall could not attribute. RESOLVED/DISMISSED
-- rows are preserved across refreshes; only PENDING rows are recomputed.
CREATE TABLE IF NOT EXISTS CC_UNATTRIBUTED (
    USER_NAME         VARCHAR(255)  NOT NULL PRIMARY KEY,
    TOKEN_CREDITS     NUMBER(20,6)  DEFAULT 0,           -- credits at risk in the window
    WAREHOUSE_CREDITS NUMBER(20,6)  DEFAULT 0,
    LAST_SEEN         DATE,
    STATUS            VARCHAR(20)   DEFAULT 'PENDING',   -- PENDING/RESOLVED/DISMISSED
    RESOLUTION_NOTES  VARCHAR(2000),
    RESOLVED_BY       VARCHAR(255),
    RESOLVED_AT       TIMESTAMP_LTZ,
    NOTED_AT          TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------------
-- 2. WAREHOUSE-CREDIT REFRESH SP  (prompt-tagged SQL → warehouse credits)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_CC_REFRESH_WAREHOUSE_USAGE(BACKFILL_DAYS NUMBER)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_rows NUMBER DEFAULT 0;
    v_attr VARCHAR;
BEGIN
    -- Recompute a trailing window (QUERY_ATTRIBUTION_HISTORY has hours of latency,
    -- so a re-merge of recent days is safer than a strict watermark).
    MERGE INTO CC_WAREHOUSE_USAGE_DAILY tgt
    USING (
        SELECT
            qh.START_TIME::DATE                                        AS USAGE_DATE,
            qh.USER_NAME                                               AS USER_NAME,
            CASE
                WHEN app ILIKE 'cortex_code_cli%'       THEN 'CLI'
                WHEN app ILIKE 'cortex_code_desktop%'   THEN 'DESKTOP'
                WHEN app ILIKE 'cortex_code_snowsight%' THEN 'SNOWSIGHT'
                WHEN app ILIKE 'cortex_code_sandbox%'   THEN 'SANDBOX'
                WHEN app ILIKE 'cortex_code_api%'       THEN 'API'
                ELSE 'OTHER'
            END                                                        AS SURFACE,
            COUNT(DISTINCT qh.QUERY_ID)                                AS QUERY_COUNT,
            SUM(qah.CREDITS_ATTRIBUTED_COMPUTE)                        AS WAREHOUSE_CREDITS
        FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY qh
        JOIN SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY qah
            ON qah.QUERY_ID = qh.QUERY_ID
        , LATERAL (SELECT TRY_PARSE_JSON(qh.QUERY_TAG):app::STRING AS app) t
        WHERE qh.START_TIME >= DATEADD('day', -1 * :BACKFILL_DAYS, CURRENT_DATE())
          AND t.app ILIKE 'cortex_code%'
          AND qah.CREDITS_ATTRIBUTED_COMPUTE > 0
        GROUP BY 1, 2, 3
    ) src
    ON  tgt.USAGE_DATE = src.USAGE_DATE
    AND tgt.USER_NAME  = src.USER_NAME
    AND tgt.SURFACE    = src.SURFACE
    WHEN MATCHED THEN UPDATE SET
        QUERY_COUNT = src.QUERY_COUNT,
        WAREHOUSE_CREDITS = src.WAREHOUSE_CREDITS,
        REFRESHED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (USAGE_DATE, USER_NAME, SURFACE, QUERY_COUNT, WAREHOUSE_CREDITS, REFRESHED_AT)
        VALUES (src.USAGE_DATE, src.USER_NAME, src.SURFACE, src.QUERY_COUNT,
                src.WAREHOUSE_CREDITS, CURRENT_TIMESTAMP());

    SELECT COUNT(*) INTO v_rows FROM CC_WAREHOUSE_USAGE_DAILY
      WHERE USAGE_DATE >= DATEADD('day', -1 * :BACKFILL_DAYS, CURRENT_DATE());

    -- Chain the waterfall so the two summaries stay in lock-step.
    CALL SP_CC_ATTRIBUTE_USAGE(:BACKFILL_DAYS) INTO :v_attr;

    RETURN 'OK: warehouse rows in window=' || v_rows || '; ' || v_attr;
END;
$$;

-- ---------------------------------------------------------------------------
-- 3. WATERFALL ATTRIBUTION SP  (trimmed: L3 svc-user > L4 user-tag > L5 role)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_CC_ATTRIBUTE_USAGE(LOOKBACK_DAYS NUMBER)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS OWNER
AS
$$
DECLARE
    v_rows NUMBER DEFAULT 0;
    v_unattr NUMBER DEFAULT 0;
BEGIN
    -- Full rebuild of the trailing window (idempotent).
    DELETE FROM CC_ATTRIBUTION_DAILY
      WHERE USAGE_DATE >= DATEADD('day', -1 * :LOOKBACK_DAYS, CURRENT_DATE());

    INSERT INTO CC_ATTRIBUTION_DAILY
        (USAGE_DATE, USER_NAME, SURFACE, ENTITY, ENTITY_TYPE, ATTR_METHOD,
         CONFIDENCE, TOKEN_CREDITS, WAREHOUSE_CREDITS, REFRESHED_AT)
    WITH tok AS (
        SELECT USAGE_DATE, USER_NAME, SURFACE, SUM(TOTAL_CREDITS) AS TOKEN_CREDITS
        FROM CC_USAGE_DAILY_SUMMARY
        WHERE USAGE_DATE >= DATEADD('day', -1 * :LOOKBACK_DAYS, CURRENT_DATE())
        GROUP BY 1, 2, 3
    ),
    wh AS (
        SELECT USAGE_DATE, USER_NAME, SURFACE, SUM(WAREHOUSE_CREDITS) AS WAREHOUSE_CREDITS
        FROM CC_WAREHOUSE_USAGE_DAILY
        WHERE USAGE_DATE >= DATEADD('day', -1 * :LOOKBACK_DAYS, CURRENT_DATE())
        GROUP BY 1, 2, 3
    ),
    base AS (
        SELECT
            COALESCE(tok.USAGE_DATE, wh.USAGE_DATE) AS USAGE_DATE,
            COALESCE(tok.USER_NAME,  wh.USER_NAME)  AS USER_NAME,
            COALESCE(tok.SURFACE,    wh.SURFACE)    AS SURFACE,
            COALESCE(tok.TOKEN_CREDITS, 0)          AS TOKEN_CREDITS,
            COALESCE(wh.WAREHOUSE_CREDITS, 0)       AS WAREHOUSE_CREDITS
        FROM tok
        FULL OUTER JOIN wh
          ON tok.USAGE_DATE = wh.USAGE_DATE
         AND tok.USER_NAME  = wh.USER_NAME
         AND tok.SURFACE    = wh.SURFACE
    ),
    -- one entity per user via role mapping (deterministic pick avoids fanout)
    role_res AS (
        SELECT USER_NAME, ENTITY, ENTITY_TYPE FROM (
            SELECT g.GRANTEE_NAME AS USER_NAME, rm.ENTITY, rm.ENTITY_TYPE,
                   ROW_NUMBER() OVER (PARTITION BY g.GRANTEE_NAME
                                      ORDER BY rm.UPDATED_AT DESC, rm.ROLE_NAME) AS rn
            FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_USERS g
            JOIN CC_ROLE_MAPPING rm ON rm.ROLE_NAME = g.ROLE AND g.DELETED_ON IS NULL
        ) WHERE rn = 1
    )
    SELECT
        b.USAGE_DATE, b.USER_NAME, b.SURFACE,
        COALESCE(su.ENTITY,
                 CASE WHEN t.VERTICAL IS NOT NULL THEN t.VERTICAL
                      WHEN t.IS_PARTNER THEN 'Partner' END,
                 r.ENTITY)                                            AS ENTITY,
        COALESCE(su.ENTITY_TYPE,
                 CASE WHEN t.VERTICAL IS NOT NULL THEN 'VERTICAL'
                      WHEN t.IS_PARTNER THEN 'PARTNER_FLAG' END,
                 r.ENTITY_TYPE)                                       AS ENTITY_TYPE,
        CASE WHEN su.ENTITY IS NOT NULL THEN 'L3_SERVICE_USER'
             WHEN t.VERTICAL IS NOT NULL OR t.IS_PARTNER THEN 'L4_USER_TAG'
             WHEN r.ENTITY IS NOT NULL THEN 'L5_ROLE'
             ELSE 'UNATTRIBUTED' END                                  AS ATTR_METHOD,
        CASE WHEN su.ENTITY IS NOT NULL THEN 'HIGH'
             WHEN t.VERTICAL IS NOT NULL OR t.IS_PARTNER THEN 'MEDIUM'
             WHEN r.ENTITY IS NOT NULL THEN 'MEDIUM'
             ELSE 'NONE' END                                          AS CONFIDENCE,
        b.TOKEN_CREDITS, b.WAREHOUSE_CREDITS, CURRENT_TIMESTAMP()
    FROM base b
    LEFT JOIN CC_SERVICE_USER_MAPPING su ON su.USER_NAME = b.USER_NAME
    LEFT JOIN CC_COST_TAGS t             ON t.USER_NAME  = b.USER_NAME
    LEFT JOIN role_res r                 ON r.USER_NAME  = b.USER_NAME;

    -- Refresh the PENDING queue for still-unattributed users (preserve resolved/dismissed).
    DELETE FROM CC_UNATTRIBUTED WHERE STATUS = 'PENDING';

    MERGE INTO CC_UNATTRIBUTED q
    USING (
        SELECT USER_NAME,
               SUM(TOKEN_CREDITS)     AS TOKEN_CREDITS,
               SUM(WAREHOUSE_CREDITS) AS WAREHOUSE_CREDITS,
               MAX(USAGE_DATE)        AS LAST_SEEN
        FROM CC_ATTRIBUTION_DAILY
        WHERE ATTR_METHOD = 'UNATTRIBUTED'
          AND USAGE_DATE >= DATEADD('day', -1 * :LOOKBACK_DAYS, CURRENT_DATE())
        GROUP BY USER_NAME
    ) s ON q.USER_NAME = s.USER_NAME
    WHEN MATCHED AND q.STATUS = 'PENDING' THEN UPDATE SET
        TOKEN_CREDITS = s.TOKEN_CREDITS, WAREHOUSE_CREDITS = s.WAREHOUSE_CREDITS,
        LAST_SEEN = s.LAST_SEEN, NOTED_AT = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN INSERT
        (USER_NAME, TOKEN_CREDITS, WAREHOUSE_CREDITS, LAST_SEEN, STATUS, NOTED_AT)
        VALUES (s.USER_NAME, s.TOKEN_CREDITS, s.WAREHOUSE_CREDITS, s.LAST_SEEN,
                'PENDING', CURRENT_TIMESTAMP());

    SELECT COUNT(*) INTO v_rows FROM CC_ATTRIBUTION_DAILY
      WHERE USAGE_DATE >= DATEADD('day', -1 * :LOOKBACK_DAYS, CURRENT_DATE());
    SELECT COUNT(*) INTO v_unattr FROM CC_UNATTRIBUTED WHERE STATUS = 'PENDING';

    RETURN 'OK: attributed ' || v_rows || ' rows; ' || v_unattr || ' users pending in queue.';
END;
$$;

-- ---------------------------------------------------------------------------
-- 4. DAILY TASK — refresh warehouse credits, then attribute (single chain)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE TASK CC_REFRESH_WAREHOUSE_USAGE
    WAREHOUSE = __WH__
    SCHEDULE  = 'USING CRON 30 3 * * * UTC'
    COMMENT   = 'Daily: roll up CoCo warehouse credits + run attribution waterfall'
AS
    CALL SP_CC_REFRESH_WAREHOUSE_USAGE(14);

ALTER TASK CC_REFRESH_WAREHOUSE_USAGE RESUME;

-- ---------------------------------------------------------------------------
-- 5. GRANTS
-- ---------------------------------------------------------------------------
GRANT USAGE ON PROCEDURE SP_CC_REFRESH_WAREHOUSE_USAGE(NUMBER) TO ROLE __APP_ROLE__;
GRANT USAGE ON PROCEDURE SP_CC_ATTRIBUTE_USAGE(NUMBER) TO ROLE __APP_ROLE__;
