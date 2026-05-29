"""
CoCo Control Hub - Stored Procedure Definitions
==========================================================
Bulk SPs that run server-side loops — avoids O(N) Python round-trips
for cohort apply (up to 50K users), bulk access grants, and
intelligent credit rebalancing.

These SPs must be EXECUTE AS OWNER with ACCOUNTADMIN ownership
because ALTER USER and GRANT DATABASE ROLE require elevated privileges.

Usage (from setup.py):
    ddl_list = get_bulk_sp_ddl(db, schema)
    for ddl in ddl_list:
        session.sql(ddl).collect()
    rebalance_ddl = get_rebalance_sp_ddl(db, schema)
    session.sql(rebalance_ddl).collect()
"""

# ---------------------------------------------------------------------------
# SP body: bulk grant SNOWFLAKE.CORTEX_USER / SNOWFLAKE.COPILOT_USER
# Accepts: USERS_JSON (VARIANT array of usernames)
#          DB_ROLES_JSON (VARIANT array of DB role FQNs, e.g. "SNOWFLAKE.CORTEX_USER")
# Returns: VARIANT {"success": N, "failed": M, "errors": [...]}
# ---------------------------------------------------------------------------
_BULK_GRANT_BODY = '''\
import re

_SAFE_ID = re.compile(r'[;\n\r\x00]')  # blocks only truly dangerous chars

def _qid(s):
    # Safely double-quote a Snowflake identifier; escapes embedded " as ""
    return '"' + str(s).replace('"', '""') + '"'

def handler(session, users_json, db_roles_json):
    out = {'success': 0, 'failed': 0, 'errors': []}
    users = list(users_json) if users_json else []
    roles = list(db_roles_json) if db_roles_json else []

    for user in users:
        user = str(user).strip()
        if not user or _SAFE_ID.search(user):
            out['errors'].append(f'Skipped invalid username: {user}')
            out['failed'] += 1
            continue
        for role in roles:
            role = str(role).strip()
            try:
                session.sql(f\'GRANT DATABASE ROLE {role} TO USER "{user}"\').collect()
                out['success'] += 1
            except Exception as e:
                out['errors'].append(f'{user}/{role}: {str(e)[:120]}')
                out['failed'] += 1

    return out
'''

# ---------------------------------------------------------------------------
# SP body: bulk set credit limits for a list of users
# Accepts: USERS_JSON (VARIANT array of usernames)
#          CLI_LIMIT (INT), SS_LIMIT (INT)
#          IS_TEMPORARY (BOOLEAN), EXPIRES_AT (VARCHAR ISO date or '')
# Returns: VARIANT {"success": N, "failed": M, "errors": [...]}
# ---------------------------------------------------------------------------
_BULK_LIMITS_BODY = '''\
import re

_SAFE_ID = re.compile(r'[;\n\r\x00]')  # blocks only truly dangerous chars

def _qid(s):
    # Safely double-quote a Snowflake identifier; escapes embedded " as ""
    return '"' + str(s).replace('"', '""') + '"'
_CLI_PARAM     = 'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER'
_SS_PARAM      = 'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER'
_DESKTOP_PARAM = 'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER'

def handler(session, users_json, cli_limit, ss_limit, dt_limit, is_temporary, expires_at):
    out = {'success': 0, 'failed': 0, 'errors': []}
    users = list(users_json) if users_json else []

    for user in users:
        user = str(user).strip()
        if not user or _SAFE_ID.search(user):
            out['errors'].append(f'Skipped invalid username: {user}')
            out['failed'] += 1
            continue
        try:
            session.sql(
                'ALTER USER ' + _qid(user) + ' SET '
                + _CLI_PARAM     + ' = ' + str(int(cli_limit))  + ', '
                + _SS_PARAM      + ' = ' + str(int(ss_limit))   + ', '
                + _DESKTOP_PARAM + ' = ' + str(int(dt_limit))
            ).collect()
            out['success'] += 1
        except Exception as e:
            out['errors'].append(f'{user}: {str(e)[:120]}')
            out['failed'] += 1

    return out
'''


def _build_sp_ddl(db: str, schema: str, sp_name: str,
                  params: str, body: str) -> str:
    """Assemble CREATE OR REPLACE PROCEDURE DDL."""
    return (
        f"CREATE OR REPLACE PROCEDURE {db}.{schema}.{sp_name}(\n"
        f"    {params}\n"
        f")\n"
        f"RETURNS VARIANT\n"
        f"LANGUAGE PYTHON\n"
        f"RUNTIME_VERSION = '3.9'\n"
        f"PACKAGES = ('snowflake-snowpark-python')\n"
        f"HANDLER = 'handler'\n"
        f"EXECUTE AS OWNER\n"
        f"AS $$\n"
        f"{body}\n"
        f"$$"
    )


def get_bulk_sp_ddl(db: str, schema: str) -> list:
    """
    Return a list of CREATE OR REPLACE PROCEDURE DDL strings for the
    two bulk SPs.  Execute each with session.sql(ddl).collect() —
    no semicolons needed when calling session.sql() directly.
    """
    return [
        _build_sp_ddl(
            db, schema,
            "SP_CC_BULK_GRANT_ACCESS",
            "USERS_JSON VARIANT, DB_ROLES_JSON VARIANT",
            _BULK_GRANT_BODY,
        ),
        _build_sp_ddl(
            db, schema,
            "SP_CC_BULK_SET_COHORT_LIMITS",
            "USERS_JSON VARIANT, CLI_LIMIT INT, SS_LIMIT INT, DT_LIMIT INT, "
            "IS_TEMPORARY BOOLEAN, EXPIRES_AT VARCHAR",
            _BULK_LIMITS_BODY,
        ),
    ]


# ---------------------------------------------------------------------------
# SP body: Server-side rebalancing with cohort-level concurrency lock
#
# Fixes two issues:
#   1. O(N) Python round-trips for SHOW PARAMETERS — moved entirely server-side
#   2. Race condition — cohort-level TTL lock prevents double-spending a donor
#
# Accepts:
#   REQUESTER VARCHAR        — username requesting credits
#   COHORT_ROLE VARCHAR      — cohort the requester belongs to
#   SURFACE VARCHAR          — CLI / SNOWSIGHT / DESKTOP
#   AMOUNT NUMBER            — credits requested
#   REASON VARCHAR           — user-provided justification
#   APPROVAL_MODE VARCHAR    — AUTO or ADMIN
#   DONOR_STRATEGY VARCHAR   — WEIGHTED_RANDOM / HIGHEST_SURPLUS / etc.
#   BUFFER_PCT NUMBER        — safety buffer (e.g. 20 = 20%)
#   MAX_TRANSFER_PCT NUMBER  — max % of donor limit transferable (e.g. 50)
#   LOOKBACK_DAYS NUMBER     — days of hourly history to use for EWMA
#   PROTECTION_HOURS NUMBER  — hours to skip recent donors (ROUND_ROBIN)
#   DB_SCHEMA VARCHAR        — 'DB.SCHEMA' — used to reference CC_* tables
#
# Returns: VARIANT {
#   "status": "APPROVED" | "PENDING" | "LOCKED" | "ERROR",
#   "message": "...",
#   "new_limit": N,          (APPROVED only)
#   "donors": [{user, reduction}],
#   "available": N,          (PENDING due to insufficient surplus)
# }
# ---------------------------------------------------------------------------
_REBALANCE_BODY = '''\
import json, re, random
from datetime import datetime

_SAFE_ID   = re.compile(r'[;\n\r\x00]')   # blocks only truly dangerous chars
_PARAM_MAP = {
    'CLI':      'CORTEX_CODE_CLI_DAILY_EST_CREDIT_LIMIT_PER_USER',
    'SNOWSIGHT':'CORTEX_CODE_SNOWSIGHT_DAILY_EST_CREDIT_LIMIT_PER_USER',
    'DESKTOP':  'CORTEX_CODE_DESKTOP_DAILY_EST_CREDIT_LIMIT_PER_USER',
}
_MIN_HISTORY_DAYS = 5
_ALPHA = 0.3


def _qid(s):
    # Safely double-quote any Snowflake identifier — handles ., @, __, ", etc.
    return '"' + str(s).replace('"', '""') + '"'


def _ewma(values):
    if not values: return 0.0
    result = float(values[0])
    for v in values[1:]:
        result = _ALPHA * float(v) + (1 - _ALPHA) * result
    return result


def _predict_remaining(user_hour_data, user, current_hour):
    remaining = list(range(current_hour + 1, 24))
    if not remaining or user not in user_hour_data:
        return 0.0
    total = 0.0
    for h in remaining:
        obs = sorted(user_hour_data[user].get(h, []))
        if obs:
            total += _ewma([c for _, c in obs])
    return max(total, 0.0)


def _select_donors(eligible, amount, strategy):
    if strategy == 'MINIMUM_DONORS':
        single = [d for d in eligible if d['transferable'] >= amount]
        if single:
            return _greedy([max(single, key=lambda x: x['transferable'])], amount)
        return _greedy(sorted(eligible, key=lambda x: x['transferable'], reverse=True), amount)
    elif strategy == 'ROUND_ROBIN':
        fresh  = sorted([d for d in eligible if not d['recent']], key=lambda x: x['transferable'], reverse=True)
        recent = sorted([d for d in eligible if d['recent']],  key=lambda x: x['transferable'], reverse=True)
        return _greedy(fresh + recent, amount)
    elif strategy == 'WEIGHTED_RANDOM':
        pool = [d for d in eligible if d['transferable'] > 0]
        tw   = sum(d['transferable'] for d in pool)
        if not tw: return _greedy(pool, amount)
        ordered, rem = [], pool[:]
        while rem:
            wts = [d['transferable'] / sum(d['transferable'] for d in rem) for d in rem]
            pick = random.choices(rem, weights=wts, k=1)[0]
            ordered.append(rem.pop(rem.index(pick)))
        return _greedy(ordered, amount)
    else:  # HIGHEST_SURPLUS
        return _greedy(sorted(eligible, key=lambda x: x['transferable'], reverse=True), amount)


def _greedy(donors, amount):
    result, need = [], amount
    for d in donors:
        if need <= 0: break
        take = min(d['transferable'], need)
        result.append({'user': d['user'], 'limit': d['limit'],
                       'new_limit': d['limit'] - take, 'reduction': take})
        need -= take
    return result


def _esc(s):
    return str(s).replace("\'", "\'\'")


def _release_lock(session, lock_tbl, cohort, requester):
    try:
        session.sql(
            f"DELETE FROM {lock_tbl} WHERE COHORT_ROLE = \'{_esc(cohort)}\' AND LOCKED_BY = \'{_esc(requester)}\'"
        ).collect()
    except Exception:
        pass


def _log_audit(session, audit_tbl, actor, action, target_user, target_role, details, old_val, new_val):
    try:
        safe_actor  = _esc(actor)
        safe_action = _esc(action)
        safe_target = f"\'{_esc(target_user)}\'" if target_user else "NULL"
        safe_role   = f"\'{_esc(target_role)}\'" if target_role else "NULL"
        safe_old    = f"\'{_esc(old_val)}\'" if old_val is not None else "NULL"
        safe_new    = f"\'{_esc(new_val)}\'" if new_val is not None else "NULL"
        safe_detail = _esc(json.dumps(details))
        session.sql(f"""
            INSERT INTO {audit_tbl}
                (TIMESTAMP, ACTOR, ACTOR_ROLE, ACTION_TYPE, TARGET_USER, TARGET_ROLE,
                 DETAILS, OLD_VALUE, NEW_VALUE, STATUS)
            SELECT CURRENT_TIMESTAMP(), \'{safe_actor}\', \'SP_OWNER\', \'{safe_action}\',
                   {safe_target}, {safe_role},
                   TRY_PARSE_JSON(\'{safe_detail}\'), {safe_old}, {safe_new}, \'SUCCESS\'
        """).collect()
    except Exception:
        pass


def handler(session, requester, cohort_role, surface, amount,
            reason, approval_mode, donor_strategy,
            buffer_pct, max_transfer_pct, lookback_days,
            protection_hours, db_schema):

    surface = str(surface).upper()
    if surface not in _PARAM_MAP:
        return {'status': 'ERROR', 'message': f'Invalid surface: {surface}'}
    if not requester or _SAFE_ID.search(str(requester)) or not cohort_role or _SAFE_ID.search(str(cohort_role)):
        return {'status': 'ERROR', 'message': 'Invalid identifier characters'}

    param       = _PARAM_MAP[surface]
    buffer      = float(buffer_pct) / 100.0
    max_cap_pct = float(max_transfer_pct) / 100.0
    lookback    = int(lookback_days)
    prot_hrs    = int(protection_hours)
    amount      = float(amount)

    lock_tbl     = f"{db_schema}.CC_COHORT_REBALANCE_LOCK"
    hourly_tbl   = f"{db_schema}.CC_USAGE_HOURLY_SUMMARY"
    audit_tbl    = f"{db_schema}.CC_AUDIT_LOG"
    requests_tbl = f"{db_schema}.CC_CREDIT_REQUESTS"
    cohort_tbl   = f"{db_schema}.CC_USER_COHORT_RESOLVED"

    safe_cohort    = _esc(cohort_role)
    safe_requester = _esc(requester)
    safe_surface   = _esc(surface)
    safe_reason    = _esc(reason or "")

    # ── Acquire lock ──────────────────────────────────────────────────────────
    lock_acquired = False
    try:
        session.sql(
            f"DELETE FROM {lock_tbl} WHERE EXPIRES_AT < CURRENT_TIMESTAMP()"
        ).collect()
        rows = session.sql(f"""
            MERGE INTO {lock_tbl} t
            USING (SELECT \'{safe_cohort}\' AS C) s ON t.COHORT_ROLE = s.C
            WHEN NOT MATCHED THEN INSERT (COHORT_ROLE, LOCKED_BY, LOCKED_AT, EXPIRES_AT)
                VALUES (\'{safe_cohort}\', \'{safe_requester}\',
                        CURRENT_TIMESTAMP(),
                        DATEADD(\'second\', 120, CURRENT_TIMESTAMP()))
        """).collect()
        lock_acquired = (rows and int(rows[0][0]) > 0)
    except Exception:
        lock_acquired = True  # lock table may not exist yet — proceed without lock

    if not lock_acquired:
        return {
            'status': 'LOCKED',
            'message': 'A rebalancing request for your cohort is already being processed. Try again in a moment.'
        }

    try:
        # ── Cohort members (one query via CC_USER_COHORT_RESOLVED) ────────────
        members_rows = session.sql(f"""
            SELECT DISTINCT USER_NAME FROM {cohort_tbl}
            WHERE COHORT_ROLE = \'{safe_cohort}\'
              AND USER_NAME != \'{safe_requester}\'
        """).collect()
        members = [r[0] for r in members_rows
                   if r[0] and _SAFE_ID.match(str(r[0]))]

        if not members:
            # Fallback: SHOW GRANTS OF ROLE (for accounts without resolved cohort table)
            try:
                grants = session.sql(f\'SHOW GRANTS OF ROLE "{cohort_role}"\').collect()
                members = [
                    r["grantee_name"].upper() for r in grants
                    if str(r.get("granted_to","")).upper() == "USER"
                    and str(r.get("grantee_name","")).upper() != requester.upper()
                    and not _SAFE_ID.search(str(r.get("grantee_name","")))
                ]
            except Exception:
                members = []

        if not members:
            _release_lock(session, lock_tbl, safe_cohort, safe_requester)
            _insert_pending(session, requests_tbl, safe_requester, safe_cohort,
                            safe_surface, amount, safe_reason)
            return {'status': 'PENDING',
                    'message': 'No cohort members found — request queued for admin review.'}

        # ── Current limits (SHOW PARAMETERS per user — server-side, no SiS timeout) ──
        current_limits = {}
        for m in members:
            try:
                rows = session.sql(
                    f\'SHOW PARAMETERS LIKE \\\'{param}\\\' IN USER "{m}"\' 
                ).collect()
                val = rows[0]["value"] if rows else None
                current_limits[m] = float(val) if val and val != "-1" else -1.0
            except Exception:
                current_limits[m] = -1.0  # treat as unlimited

        # Requester current limit
        try:
            rows = session.sql(
                f\'SHOW PARAMETERS LIKE \\\'{param}\\\' IN USER "{requester}"\' 
            ).collect()
            val = rows[0]["value"] if rows else None
            requester_limit = float(val) if val and val != "-1" else -1.0
        except Exception:
            requester_limit = -1.0

        # ── Today usage — single query for ALL members ────────────────────────
        all_in = ", ".join([f"\'{_esc(m)}\'" for m in members])
        today_rows = session.sql(f"""
            SELECT USER_NAME, SUM(TOTAL_CREDITS) AS CR
            FROM {hourly_tbl}
            WHERE USAGE_DATE = CURRENT_DATE()
              AND SURFACE = \'{safe_surface}\'
              AND USER_NAME IN ({all_in})
            GROUP BY USER_NAME
        """).collect()
        today_usage = {r[0]: float(r[1] or 0) for r in today_rows}

        # ── Hourly history — single query for EWMA ────────────────────────────
        hist_rows = session.sql(f"""
            SELECT USER_NAME, USAGE_DATE, USAGE_HOUR, TOTAL_CREDITS
            FROM {hourly_tbl}
            WHERE USAGE_DATE >= DATEADD(\'day\', -{lookback}, CURRENT_DATE())
              AND USAGE_DATE < CURRENT_DATE()
              AND SURFACE = \'{safe_surface}\'
              AND USER_NAME IN ({all_in})
            ORDER BY USER_NAME, USAGE_DATE, USAGE_HOUR
        """).collect()

        # Build {user: {hour: [(date, credits), ...]}} and unique-date count
        user_hour_data = {}
        user_dates     = {}
        for r in hist_rows:
            u, d, h, c = r[0], str(r[1]), int(r[2]), float(r[3] or 0)
            user_hour_data.setdefault(u, {}).setdefault(h, []).append((d, c))
            user_dates.setdefault(u, set()).add(d)

        # ── Recent donors for ROUND_ROBIN ──────────────────────────────────────
        recent_donors = set()
        if donor_strategy.upper() == "ROUND_ROBIN" and prot_hrs > 0:
            try:
                rd_rows = session.sql(f"""
                    SELECT DISTINCT TARGET_USER FROM {audit_tbl}
                    WHERE ACTION_TYPE = \'REBALANCE_REDUCE\'
                      AND TIMESTAMP >= DATEADD(\'hour\', -{prot_hrs}, CURRENT_TIMESTAMP())
                      AND TARGET_USER IS NOT NULL
                """).collect()
                recent_donors = {r[0].upper() for r in rd_rows if r[0]}
            except Exception:
                pass

        # ── Compute surplus per member ─────────────────────────────────────────
        current_hour = datetime.utcnow().hour
        eligible = []

        for m in members:
            limit = current_limits.get(m, -1.0)
            if limit <= 0:   # unlimited (-1) or blocked (0) — skip as donor
                continue
            unique_dates = len(user_dates.get(m, set()))
            if unique_dates < _MIN_HISTORY_DAYS:
                continue    # cold-start guard
            used      = today_usage.get(m, 0.0)
            predicted = _predict_remaining(user_hour_data, m, current_hour)
            raw_surplus  = limit - used - predicted
            safe_surplus = max(raw_surplus - limit * buffer, 0.0)
            transferable = round(min(safe_surplus, limit * max_cap_pct), 2)
            if transferable > 0:
                eligible.append({
                    'user': m, 'limit': limit,
                    'transferable': transferable,
                    'recent': m.upper() in recent_donors,
                })

        total_available = sum(d['transferable'] for d in eligible)

        if total_available < amount:
            _release_lock(session, lock_tbl, safe_cohort, safe_requester)
            _insert_pending(session, requests_tbl, safe_requester, safe_cohort,
                            safe_surface, amount, safe_reason)
            return {
                'status': 'PENDING',
                'message': f'Only {total_available:.1f} credits available in cohort ({amount:.0f} requested). Queued for admin review.',
                'available': total_available,
            }

        donors = _select_donors(eligible, amount, str(donor_strategy).upper())

        if str(approval_mode).upper() == "AUTO":
            # Apply donor reductions
            for d in donors:
                new_lim = int(round(d['new_limit']))
                session.sql(
                    'ALTER USER ' + _qid(d['user']) + ' SET ' + param + ' = ' + str(new_lim)
                ).collect()
                _log_audit(session, audit_tbl, requester, 'REBALANCE_REDUCE',
                           d['user'], cohort_role,
                           {'surface': surface, 'requester': requester, 'reduction': d['reduction']},
                           str(int(d['limit'])), str(new_lim))

            # Apply requester increase
            new_req_limit = int(round((requester_limit if requester_limit > 0 else 0) + amount))
            session.sql(
                'ALTER USER ' + _qid(requester) + ' SET ' + param + ' = ' + str(new_req_limit)
            ).collect()
            _log_audit(session, audit_tbl, requester, 'REBALANCE_INCREASE',
                       requester, cohort_role,
                       {'surface': surface, 'donors': [d['user'] for d in donors]},
                       str(int(requester_limit)) if requester_limit > 0 else '0',
                       str(new_req_limit))

            donor_str = donors[0]['user'] if donors else 'AUTO'
            _insert_approved(session, requests_tbl, safe_requester, safe_cohort,
                             safe_surface, amount, safe_reason, donor_str)
            _release_lock(session, lock_tbl, safe_cohort, safe_requester)

            return {
                'status': 'APPROVED',
                'new_limit': new_req_limit,
                'amount': amount,
                'donors': [{'user': d['user'], 'reduction': d['reduction']} for d in donors],
                'message': f"Approved. +{int(amount)} {surface} credits. New limit: {new_req_limit}.",
            }

        else:  # ADMIN mode — queue for review
            _insert_pending(session, requests_tbl, safe_requester, safe_cohort,
                            safe_surface, amount, safe_reason)
            _release_lock(session, lock_tbl, safe_cohort, safe_requester)
            return {
                'status': 'PENDING',
                'message': 'Request queued for admin review.',
                'recommendation': {
                    'feasible': True,
                    'available': total_available,
                    'donors': [{'user': d['user'], 'reduction': d['transferable']} for d in donors[:3]],
                },
            }

    except Exception as e:
        _release_lock(session, lock_tbl, safe_cohort, safe_requester)
        return {'status': 'ERROR', 'message': str(e)[:300]}


def _insert_pending(session, tbl, requester, cohort, surface, amount, reason):
    session.sql(f"""
        INSERT INTO {tbl}
            (REQUEST_TIMESTAMP, REQUESTER, COHORT_ROLE, SURFACE,
             AMOUNT_REQUESTED, REASON, STATUS)
        SELECT CURRENT_TIMESTAMP(), \'{requester}\', \'{cohort}\', \'{surface}\',
               {amount}, \'{reason}\', \'PENDING\'
    """).collect()


def _insert_approved(session, tbl, requester, cohort, surface,
                     amount, reason, donor):
    safe_donor = _esc(donor)
    session.sql(f"""
        INSERT INTO {tbl}
            (REQUEST_TIMESTAMP, REQUESTER, COHORT_ROLE, SURFACE,
             AMOUNT_REQUESTED, AMOUNT_APPROVED, REASON, DONOR_USER,
             STATUS, APPROVED_BY, APPROVED_AT)
        SELECT CURRENT_TIMESTAMP(), \'{requester}\', \'{cohort}\', \'{surface}\',
               {amount}, {amount}, \'{reason}\', \'{safe_donor}\',
               \'APPROVED\', \'AUTO\', CURRENT_TIMESTAMP()
    """).collect()
'''


def get_rebalance_sp_ddl(db: str, schema: str) -> str:
    """
    Returns CREATE OR REPLACE PROCEDURE DDL for SP_CC_COMPUTE_REBALANCE.
    Execute with session.sql(ddl).collect() — no semicolons needed.
    """
    return _build_sp_ddl(
        db, schema,
        "SP_CC_COMPUTE_REBALANCE",
        (
            "REQUESTER VARCHAR, COHORT_ROLE VARCHAR, SURFACE VARCHAR, "
            "AMOUNT NUMBER, REASON VARCHAR, APPROVAL_MODE VARCHAR, "
            "DONOR_STRATEGY VARCHAR, BUFFER_PCT NUMBER, MAX_TRANSFER_PCT NUMBER, "
            "LOOKBACK_DAYS NUMBER, PROTECTION_HOURS NUMBER, DB_SCHEMA VARCHAR"
        ),
        _REBALANCE_BODY,
    )
