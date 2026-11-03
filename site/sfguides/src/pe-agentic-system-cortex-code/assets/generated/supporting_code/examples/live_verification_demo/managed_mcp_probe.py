"""Capture real tools/list and tools/call through a caller-authenticated MCP session.

No transport, credentials, OAuth configuration or network connection is created
here. The caller must connect its approved MCP client to Snowflake-managed MCP.
"""

from datetime import datetime, timezone
import re
import time
from urllib.parse import urlsplit


def validate_endpoint(endpoint, approved_host):
    parsed = urlsplit(endpoint)
    if (parsed.scheme != "https" or parsed.hostname != approved_host
            or not approved_host.endswith(".snowflakecomputing.com")
            or "_" in approved_host or parsed.username or parsed.password
            or parsed.port not in (None, 443) or parsed.query or parsed.fragment
            or not re.fullmatch(r"/api/v2/databases/[A-Za-z_][A-Za-z0-9_]*/schemas/"
                                r"[A-Za-z_][A-Za-z0-9_]*/mcp-servers/[A-Za-z_][A-Za-z0-9_]*", parsed.path)):
        raise ValueError("Expected the explicitly approved Snowflake-managed MCP endpoint")


def record_object(value):
    return value.model_dump(mode="json", by_alias=True) if hasattr(value, "model_dump") else dict(value)


async def probe(session, *, endpoint, approved_host, approved=False, evidence=None):
    """Session must already be authenticated to endpoint. Evidence survives errors.

    The caller attests to the transport endpoint; this function cannot verify an
    arbitrary injected session's destination. Retain the client connection trace.
    """
    if not approved:
        raise PermissionError("Managed MCP calls require explicit approval")
    validate_endpoint(endpoint, approved_host)
    if evidence is None:
        evidence = []

    async def capture(method, arguments, operation):
        event = {"method": method, "arguments": arguments, "endpoint": endpoint,
                 "utc": datetime.now(timezone.utc).isoformat(),
                 "execution_kind": "mcp_client_session_transport_attested_by_caller"}
        start = time.perf_counter()
        try:
            response = record_object(await operation())
            event.update(response=response, status="tool_error" if response.get("isError") else "ok")
            return response
        except Exception as exc:
            event.update(status="error", error_type=type(exc).__name__)
            raise
        finally:
            event["latency_ms"] = (time.perf_counter() - start) * 1000
            evidence.append(event)

    inventory = await capture("tools/list", {}, session.list_tools)
    if inventory.get("nextCursor"):
        raise ValueError("Review the entire paginated tool inventory before proceeding")
    tools = inventory.get("tools", [])
    if [tool.get("name") for tool in tools] != ["review_distribution_reconciliation"]:
        raise ValueError("Unexpected tool inventory; no calls issued")
    schema = tools[0].get("inputSchema", {})
    if (schema.get("type") != "object" or set(schema.get("properties", {})) != {"P_CASE_ID"}
            or schema["properties"]["P_CASE_ID"].get("type") != "string"
            or schema.get("required") != ["P_CASE_ID"]):
        raise ValueError("Unexpected tool signature; no calls issued")
    for case in ("BALANCED", "SHORTFALL", "UNKNOWN"):
        arguments = {"P_CASE_ID": case}
        result = await capture("tools/call", arguments,
                               lambda: session.call_tool("review_distribution_reconciliation", arguments=arguments))
        if result.get("isError"):
            raise RuntimeError("MCP tool returned an error; retained in evidence")
    return evidence