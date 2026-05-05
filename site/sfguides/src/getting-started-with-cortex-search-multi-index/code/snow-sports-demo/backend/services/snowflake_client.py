"""
Snowflake Connection Manager
----------------------------
Singleton-style connection manager for Snowflake.
Supports three auth modes:
  1. connections.toml (local dev) — reads ~/.snowflake/connections.toml
  2. OAuth token auth (SPCS deployment) via /snowflake/session/token file
  3. Environment variable fallback (password, externalbrowser, key-pair)
"""

import os
import logging
from pathlib import Path
from contextlib import contextmanager

import snowflake.connector

logger = logging.getLogger(__name__)

# SPCS token file path — present when running inside Snowpark Container Services
_SPCS_TOKEN_PATH = Path("/snowflake/session/token")

# Module-level connection cache
_connection: snowflake.connector.SnowflakeConnection | None = None

# Module-level Snowpark session cache (used by Cortex Search SDK via snowflake.core.Root)
_snowpark_session = None


def _is_spcs() -> bool:
    """Detect if we're running inside Snowpark Container Services."""
    return _SPCS_TOKEN_PATH.exists()


def _load_private_key(key_path: str) -> bytes:
    """Load a PEM private key file and return DER-encoded bytes for the connector."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    key_path = os.path.expanduser(key_path)
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    return private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _load_from_toml() -> dict | None:
    """
    Try to load connection config from ~/.snowflake/connections.toml.
    Uses SNOWFLAKE_CONNECTION env var or the default_connection_name from the file.
    Returns None if the file doesn't exist.
    """
    toml_path = Path.home() / ".snowflake" / "connections.toml"
    if not toml_path.exists():
        return None

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    with open(toml_path, "rb") as f:
        config = tomllib.load(f)

    # Pick the connection name
    conn_name = os.getenv("SNOWFLAKE_CONNECTION", config.get("default_connection_name", ""))
    if not conn_name or conn_name not in config:
        return None

    conn_cfg = config[conn_name]
    logger.info("Loading connection '%s' from connections.toml", conn_name)

    params: dict = {
        "account": conn_cfg["account"],
        "user": conn_cfg["user"],
        "database": os.getenv("SNOWFLAKE_DATABASE", "CATALOG_SEARCH_DB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "APP"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", conn_cfg.get("warehouse", "CATALOG_SEARCH_WH")),
    }

    if conn_cfg.get("role"):
        params["role"] = conn_cfg["role"]

    authenticator = conn_cfg.get("authenticator", "").upper()

    if authenticator == "SNOWFLAKE_JWT" and conn_cfg.get("private_key_file"):
        # Key-pair authentication
        params["private_key"] = _load_private_key(conn_cfg["private_key_file"])
        logger.info("Using key-pair (JWT) authentication")
    elif authenticator == "EXTERNALBROWSER":
        params["authenticator"] = "externalbrowser"
        logger.info("Using externalbrowser authentication")
    elif conn_cfg.get("password"):
        params["password"] = conn_cfg["password"]
        logger.info("Using password-based authentication from toml")
    else:
        logger.warning("No supported auth method found in connection '%s'", conn_name)
        return None

    host = conn_cfg.get("host")
    if host:
        params["host"] = host

    return params


def _build_connection_params() -> dict:
    """Build Snowflake connection parameters, trying toml first, then env vars."""
    if _is_spcs():
        # SPCS: use OAuth token from the mounted secret file
        token = _SPCS_TOKEN_PATH.read_text().strip()
        params = {
            "host": os.environ["SNOWFLAKE_HOST"],
            "account": os.environ["SNOWFLAKE_ACCOUNT"],
            "authenticator": "oauth",
            "token": token,
            "database": os.getenv("SNOWFLAKE_DATABASE", "CATALOG_SEARCH_DB"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "APP"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CATALOG_SEARCH_WH"),
        }
        logger.info("Using SPCS OAuth token authentication")
        return params

    # Try connections.toml first
    toml_params = _load_from_toml()
    if toml_params:
        return toml_params

    # Fallback: environment variables
    params = {
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "database": os.getenv("SNOWFLAKE_DATABASE", "CATALOG_SEARCH_DB"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "APP"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "CATALOG_SEARCH_WH"),
    }

    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "").lower()
    if authenticator == "externalbrowser":
        params["authenticator"] = "externalbrowser"
        logger.info("Using externalbrowser authentication (env)")
    else:
        params["password"] = os.environ["SNOWFLAKE_PASSWORD"]
        logger.info("Using password-based authentication (env)")

    host = os.getenv("SNOWFLAKE_HOST")
    if host:
        params["host"] = host

    return params


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """
    Return a cached Snowflake connector connection, creating one if needed.
    Used by product catalog routes which use cursor-based SQL queries.
    """
    global _connection
    if _connection is None or _connection.is_closed():
        params = _build_connection_params()
        _connection = snowflake.connector.connect(**params)
        logger.info("Snowflake connector connection established")
    return _connection


def get_snowpark_session():
    """
    Return a cached Snowpark Session, creating one if needed.
    Snowflake Cortex Search SDK (snowflake.core.Root) requires a Snowpark session
    rather than a plain connector connection.
    Uses the same auth resolution logic as get_connection().
    """
    global _snowpark_session
    if _snowpark_session is not None:
        # Check if the underlying connection is still alive
        try:
            _snowpark_session.sql("SELECT 1").collect()
            return _snowpark_session
        except Exception:
            logger.warning("Snowpark session appears stale — recreating")
            _snowpark_session = None

    from snowflake.snowpark import Session

    params = _build_connection_params()

    # Snowpark Session builder uses slightly different param names than the connector
    builder_params = {
        "account": params["account"],
        "database": params["database"],
        "schema": params["schema"],
        "warehouse": params["warehouse"],
    }

    if "host" in params:
        builder_params["host"] = params["host"]
    if "role" in params:
        builder_params["role"] = params["role"]
    # user is required for all auth modes except SPCS OAuth token
    if params.get("user"):
        builder_params["user"] = params["user"]

    # Auth modes
    if params.get("authenticator") == "oauth":
        builder_params["authenticator"] = "oauth"
        builder_params["token"] = params["token"]
    elif params.get("authenticator") == "externalbrowser":
        builder_params["authenticator"] = "externalbrowser"
    elif "private_key" in params:
        builder_params["private_key"] = params["private_key"]
    else:
        builder_params["password"] = params["password"]

    _snowpark_session = Session.builder.configs(builder_params).create()
    logger.info("Snowpark session established")
    return _snowpark_session


def execute_query(sql: str, params: tuple | list | dict | None = None) -> list[dict]:
    """
    Execute a SQL query and return results as a list of dicts.
    Uses parameterized queries (pyformat binding) to prevent SQL injection.
    """
    conn = get_connection()
    cur = conn.cursor(snowflake.connector.DictCursor)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


@contextmanager
def get_cursor():
    """Context manager that yields a DictCursor and closes it automatically."""
    conn = get_connection()
    cur = conn.cursor(snowflake.connector.DictCursor)
    try:
        yield cur
    finally:
        cur.close()


def close_connection() -> None:
    """Close cached connections (called on app shutdown)."""
    global _connection, _snowpark_session

    if _connection and not _connection.is_closed():
        _connection.close()
        logger.info("Snowflake connector connection closed")
    _connection = None

    if _snowpark_session is not None:
        try:
            _snowpark_session.close()
            logger.info("Snowpark session closed")
        except Exception:
            pass
    _snowpark_session = None
