"""
Cortex Code Credit Manager - Audit Logging
============================================
Every action in the app is logged to CC_AUDIT_LOG via direct INSERT.
"""

import json
from typing import Any, Dict, Optional

from config import (
    TABLE_AUDIT_LOG,
    escape_sql_literal,
    fq_table,
    get_current_role,
    get_current_user,
    sanitize_identifier,
)


def log_activity(
    session,
    action_type: str,
    target_user: Optional[str] = None,
    target_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    status: str = "SUCCESS",
) -> bool:
    actor = get_current_user(session)
    actor_role = get_current_role(session)
    tbl = fq_table(session, TABLE_AUDIT_LOG)

    details_json = "NULL"
    if details:
        safe_json = escape_sql_literal(json.dumps(details, default=str))
        details_json = f"PARSE_JSON('{safe_json}')"

    target_user_sql = f"'{escape_sql_literal(target_user)}'" if target_user else "NULL"
    target_role_sql = f"'{escape_sql_literal(target_role)}'" if target_role else "NULL"
    old_val_sql = f"'{escape_sql_literal(old_value)}'" if old_value else "NULL"
    new_val_sql = f"'{escape_sql_literal(new_value)}'" if new_value else "NULL"
    safe_action = escape_sql_literal(action_type)
    safe_status = escape_sql_literal(status)

    sql = f"""
        INSERT INTO {tbl}
            (TIMESTAMP, ACTOR, ACTOR_ROLE, ACTION_TYPE, TARGET_USER, TARGET_ROLE,
             DETAILS, OLD_VALUE, NEW_VALUE, STATUS)
        SELECT
            CURRENT_TIMESTAMP(), '{escape_sql_literal(actor)}',
             '{escape_sql_literal(actor_role)}', '{safe_action}',
             {target_user_sql}, {target_role_sql},
             {details_json}, {old_val_sql}, {new_val_sql}, '{safe_status}'
    """
    try:
        session.sql(sql).collect()
        return True
    except Exception:
        return False
