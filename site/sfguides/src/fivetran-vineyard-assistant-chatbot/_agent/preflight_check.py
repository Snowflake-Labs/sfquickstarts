#!/usr/bin/env python3
"""Preflight check for the Vineyard Assistant agent runbook.

Run this before an agent follows vineyard-assistant-agent-runbook.md.
It checks that the Fivetran API still has the endpoints and fields the
runbook uses, that the connector config docs still list the parameters
the runbook sends, and (if you give it credentials) that your Fivetran
key works. It only sends read-only requests and never prints secrets.

Standard library only. Python 3.8 or later.

  python3 preflight_check.py                 # public checks only
  FIVETRAN_API_KEY=... FIVETRAN_API_SECRET=... python3 preflight_check.py

Exit code 0 means no FAIL results (WARN results need a human look).
Exit code 1 means at least one FAIL: stop and update the runbook first.
"""
import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

OPENAPI_URL = "https://fivetran.com/assets-docs/openapi/file_v1.json"
API_BASE = "https://api.fivetran.com"

# Method and path pairs the runbook calls. Path parameter names are
# ignored when comparing, so {connectionId} and {connection_id} match.
EXPECTED_ENDPOINTS = [
    ("get", "/v1/account/info"),
    ("get", "/v1/groups"),
    ("get", "/v1/destinations"),
    ("post", "/v1/destinations"),
    ("post", "/v1/destinations/{}/test"),
    ("post", "/v1/connections"),
    ("get", "/v1/connections/{}"),
    ("patch", "/v1/connections/{}"),
    ("post", "/v1/connections/{}/test"),
    ("post", "/v1/connections/{}/sync"),
]

# Top level fields the runbook sends when it creates a connection. These
# live in the shared base request schema.
CREATE_CONNECTION_FIELDS = [
    "group_id", "service", "paused", "run_setup_tests",
    "trust_certificates", "sync_frequency", "destination_schema_names",
]

# Destination request: top level fields and config fields the runbook sends.
CREATE_DESTINATION_FIELDS = [
    "group_id", "service", "region", "time_zone_offset", "run_setup_tests",
]
CREATE_DESTINATION_CONFIG_FIELDS = {
    "snowflake": ["auth", "host", "port", "database", "user", "private_key",
                  "role", "default_virtual_warehouse"],
}

# Config fields the runbook sends, per connector service. The create request
# is a family of schemas picked by the "service" value, so these are checked
# against that service's own request schema, not the shared base.
CREATE_CONFIG_FIELDS = {
    "postgres": ["schema_prefix", "host", "port", "database", "user", "password",
                 "connection_type", "update_method", "delete_capture_enabled"],
    "s3": ["schema", "table_group_name", "bucket", "prefix", "auth_type",
           "is_public", "file_type", "json_delivery_mode",
           "file_mapping_method", "files"],
}

# Pages that list connector config parameters, and the words the runbook
# relies on. A missing word means the page changed and the runbook needs a look.
DOC_CHECKS = [
    ("PostgreSQL connector config",
     "https://fivetran.com/docs/connectors/databases/postgresql/setup-guide/api-configuration",
     ["schema_prefix", "host", "port", "database", "user", "password",
      "update_method", "QUERY_BASED", "connection_type", "delete_capture_enabled"]),
    ("Amazon S3 connector config",
     "https://fivetran.com/docs/connectors/files/amazon-s3/api-configuration",
     ["table_group_name", "bucket", "prefix", "auth_type", "PUBLIC_BUCKET",
      "file_type", "json_delivery_mode", "file_mapping_method",
      "DEFINE_PER_TABLE", "files", "table_name", "file_pattern"]),
    ("Snowflake destination config",
     "https://fivetran.com/docs/destinations/snowflake/api-configuration",
     ["host", "port", "database", "auth", "KEY_PAIR", "private_key", "role",
      "default_virtual_warehouse"]),
    ("Create connection reference",
     "https://fivetran.com/docs/rest-api/api-reference/connections/create-connection",
     ["destination_schema_names", "FIVETRAN_NAMING", "run_setup_tests",
      "trust_certificates"]),
]

results = []


def record(status, name, detail=""):
    results.append((status, name, detail))
    print(f"{status:4}  {name}" + (f"  ({detail})" if detail else ""))


def http_get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def norm_path(path):
    return re.sub(r"\{[^}]*\}", "{}", path)


def resolve(spec, node, depth=0):
    """Follow $ref and merge allOf so we can read a schema's properties.

    The config object is split across several allOf parts (connector config,
    schema naming, extra keys), so the properties of every part's "config"
    are merged into one under merged["config_properties"].
    """
    if depth > 10 or not isinstance(node, dict):
        return {"properties": {}, "config_properties": {}, "required_all": []}
    if "$ref" in node:
        target = spec
        for part in node["$ref"].lstrip("#/").split("/"):
            target = target.get(part, {}) if isinstance(target, dict) else {}
        return resolve(spec, target, depth + 1)
    merged = dict(node)
    props = dict(node.get("properties", {}))
    cfg = {}
    required = set(node.get("required", []))

    def add_config(prop):
        sub = resolve(spec, prop, depth + 1)
        cfg.update(sub.get("properties", {}))

    if "config" in props:
        add_config(props["config"])
    for part in node.get("allOf", []):
        sub = resolve(spec, part, depth + 1)
        props.update(sub.get("properties", {}))
        cfg.update(sub.get("config_properties", {}))
        required |= set(sub.get("required_all", []))
        if "config" in sub.get("properties", {}):
            add_config(sub["properties"]["config"])
    merged["properties"] = props
    merged["config_properties"] = cfg
    merged["required_all"] = sorted(required)
    return merged


def service_schema(spec, base_schema, service):
    """Find the request schema for one service through the discriminator."""
    mapping = base_schema.get("discriminator", {}).get("mapping", {})
    ref = mapping.get(service) or f"#/components/schemas/{service}_NewConnectorRequestV1"
    return resolve(spec, {"$ref": ref})


def check_openapi(args):
    try:
        if args.openapi_file:
            with open(args.openapi_file, encoding="utf-8") as fh:
                spec = json.load(fh)
        else:
            spec = json.loads(http_get(args.openapi_url))
    except Exception as exc:  # network, JSON, file errors
        record("FAIL", "OpenAPI spec download", str(exc)[:120])
        return
    record("PASS", "OpenAPI spec download", f"version {spec.get('info', {}).get('version', '?')}")

    paths = {}
    for raw_path, item in spec.get("paths", {}).items():
        paths.setdefault(norm_path(raw_path), {}).update(item)
    for method, path in EXPECTED_ENDPOINTS:
        if method in paths.get(path, {}):
            record("PASS", f"endpoint {method.upper()} {path}")
        else:
            record("FAIL", f"endpoint {method.upper()} {path}", "not in the spec")

    create = paths.get("/v1/connections", {}).get("post", {})
    body = (create.get("requestBody", {}).get("content", {})
            .get("application/json", {}).get("schema", {}))
    base = resolve(spec, body)
    props = base.get("properties", {})
    if not props:
        record("WARN", "create connection fields", "could not read the request schema, check by hand")
        return
    for field in CREATE_CONNECTION_FIELDS:
        if field in props:
            record("PASS", f"create connection field {field}")
        else:
            record("FAIL", f"create connection field {field}", "not in the request schema")

    for service, fields in CREATE_CONFIG_FIELDS.items():
        check_service_request(spec, base, "connection", service, fields,
                              CREATE_CONNECTION_FIELDS)

    dest = paths.get("/v1/destinations", {}).get("post", {})
    dbody = (dest.get("requestBody", {}).get("content", {})
             .get("application/json", {}).get("schema", {}))
    dbase = resolve(spec, dbody)
    for field in CREATE_DESTINATION_FIELDS:
        if field in dbase.get("properties", {}):
            record("PASS", f"create destination field {field}")
        else:
            record("FAIL", f"create destination field {field}", "not in the request schema")
    for service, fields in CREATE_DESTINATION_CONFIG_FIELDS.items():
        check_service_request(spec, dbase, "destination", service, fields,
                              CREATE_DESTINATION_FIELDS)


def check_service_request(spec, base, kind, service, config_fields, sent_top):
    """Check one service's request schema against what the runbook sends.

    Two things must hold: every config field the runbook sends exists, and
    every field the API marks as required is one the runbook sends.
    """
    suffix = "NewConnectorRequestV1" if kind == "connection" else "NewDestinationRequest"
    mapping = base.get("discriminator", {}).get("mapping", {})
    ref = mapping.get(service) or f"#/components/schemas/{service}_{suffix}"
    svc = resolve(spec, {"$ref": ref})
    label = f"create {kind} ({service})"
    if "config" not in svc.get("properties", {}):
        record("FAIL", label, "no config object in the request schema for this service")
        return
    cfg = svc.get("config_properties", {})
    missing = [f for f in config_fields if f not in cfg]
    if missing:
        record("FAIL", label, "config fields missing: " + ", ".join(missing))
    else:
        record("PASS", label, f"{len(config_fields)} config fields found")
    unsent = [f for f in svc.get("required_all", []) if f not in sent_top and f != "config"]
    if unsent:
        record("FAIL", f"{label} required fields", "the API requires, the runbook does not send: " + ", ".join(unsent))
    else:
        record("PASS", f"{label} required fields", "all required fields are in the runbook payload")


def check_docs():
    for name, url, terms in DOC_CHECKS:
        try:
            text = http_get(url)
        except Exception as exc:
            record("WARN", f"docs page {name}", f"could not fetch: {str(exc)[:80]}")
            continue
        missing = [t for t in terms if t not in text]
        if missing:
            record("FAIL", f"docs page {name}", "missing: " + ", ".join(missing))
        else:
            record("PASS", f"docs page {name}", f"{len(terms)} terms found")


def check_live():
    key = os.environ.get("FIVETRAN_API_KEY")
    secret = os.environ.get("FIVETRAN_API_SECRET")
    if not (key and secret):
        record("SKIP", "Fivetran key check", "set FIVETRAN_API_KEY and FIVETRAN_API_SECRET to enable")
        return
    token = base64.b64encode(f"{key}:{secret}".encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Accept": "application/json"}
    for label, path in (("account info", "/v1/account/info"), ("groups", "/v1/groups?limit=100")):
        try:
            data = json.loads(http_get(API_BASE + path, headers))
            if data.get("code") == "Success":
                extra = ""
                if label == "groups":
                    items = data.get("data", {}).get("items", [])
                    extra = ", ".join(f"{i.get('name')}={i.get('id')}" for i in items[:5])
                record("PASS", f"live GET {path.split('?')[0]}", extra)
            else:
                record("FAIL", f"live GET {path.split('?')[0]}", str(data.get("code")))
        except urllib.error.HTTPError as exc:
            record("FAIL", f"live GET {path.split('?')[0]}", f"HTTP {exc.code}")
        except Exception as exc:
            record("FAIL", f"live GET {path.split('?')[0]}", str(exc)[:80])


def check_snowflake(connection=None):
    snow = shutil.which("snow")
    if not snow:
        record("SKIP", "Snowflake CLI check", "snow CLI not installed, the agent will use another SQL route")
        return
    connection = connection or os.environ.get("SNOWFLAKE_CONNECTION")
    cmd = [snow, "sql", "-q",
           "SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_REGION()",
           "--format", "json"]
    if connection:
        cmd[2:2] = ["-c", connection]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            who = ""
            try:
                row = list(json.loads(out.stdout)[0].values())
                who = "account {}, user {}, role {}, region {}".format(*row)
            except Exception:
                pass
            if connection:
                record("PASS", f"Snowflake CLI query via connection {connection}", who)
            else:
                record("WARN", "Snowflake CLI query via the DEFAULT connection",
                       (who + "; " if who else "") + "confirm this is the account you want, or pass --snow-connection NAME")
        else:
            record("FAIL", "Snowflake CLI query", out.stderr.strip()[:100])
    except Exception as exc:
        record("FAIL", "Snowflake CLI query", str(exc)[:100])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--openapi-url", default=OPENAPI_URL)
    parser.add_argument("--openapi-file", help="read the OpenAPI JSON from a local file instead")
    parser.add_argument("--skip-docs", action="store_true", help="skip the docs page checks")
    parser.add_argument("--snow-connection", help="name of the Snowflake CLI connection to test (otherwise the default one is used and a WARN is shown)")
    parser.add_argument("--json", action="store_true", help="print a JSON summary at the end")
    args = parser.parse_args()

    check_openapi(args)
    if not args.skip_docs:
        check_docs()
    check_live()
    check_snowflake(args.snow_connection)

    counts = {s: sum(1 for r in results if r[0] == s) for s in ("PASS", "WARN", "FAIL", "SKIP")}
    print("\nSummary: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    if args.json:
        print(json.dumps([{"status": s, "check": n, "detail": d} for s, n, d in results], indent=2))
    if counts["FAIL"]:
        print("Result: DRIFT FOUND. Do not run the runbook until it is updated.")
        return 1
    print("Result: OK" + (" (review the WARN lines)" if counts["WARN"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
