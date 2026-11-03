#!/bin/bash
# =============================================================================
# MCP Server Connectivity Test Script
# =============================================================================
# Tests that your Snowflake MCP Server endpoint is reachable and responding.
#
# IMPORTANT: If your account URL contains underscores, replace them with hyphens
#            in the hostname (e.g., myorg-my_account -> myorg-my-account).
#            MCP servers have connection issues with underscores in hostnames.
#            See: https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp#mcp-server-security-recommendations
#
# Usage:
#   chmod +x test-mcp-connectivity.sh
#   ./test-mcp-connectivity.sh <MCP_ENDPOINT_URL> <PAT_TOKEN>
#
# Example:
#   ./test-mcp-connectivity.sh \
#     "https://myorg-myaccount.snowflakecomputing.com/api/v2/databases/LOGISTICS_C/schemas/SHIPPING_MARTS/mcp-servers/SHIPPING_MCP_SERVER" \
#     "ver:1:abc123..."
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------

MCP_URL="${1:?Error: MCP endpoint URL required as first argument}"
PAT_TOKEN="${2:?Error: PAT token required as second argument}"

echo "============================================="
echo "Snowflake MCP Server Connectivity Test"
echo "============================================="
echo ""
echo "Endpoint: ${MCP_URL}"
echo ""

# ---------------------------------------------------------------------------
# Test 1: List available tools (tools/list)
# ---------------------------------------------------------------------------

echo "--- Test 1: Discovering tools (tools/list) ---"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MCP_URL}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer ${PAT_TOKEN}" \
  -H "X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "SUCCESS (HTTP 200)"
  echo ""
  echo "Tools discovered:"
  echo "$BODY" | python3 -c "
import sys, json
try:
    raw = sys.stdin.read()
    # Handle control characters that Snowflake may include in descriptions
    cleaned = raw.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
    data = json.loads(cleaned, strict=False)
    tools = data.get('result', {}).get('tools', [])
    if tools:
        for t in tools:
            print(f\"  - {t.get('name', 'unnamed')}: {t.get('description', '')[:80]}...\")
    else:
        print('  (no tools found in response)')
except Exception as e:
    # Fallback: extract tool names with grep
    import re
    names = re.findall(r'\"name\"\s*:\s*\"([^\"]+)\"', raw)
    if names:
        for n in names:
            print(f'  - {n}')
    else:
        print(f'  Could not parse response: {e}')
" 2>/dev/null || echo "  $BODY"
else
  echo "FAILED (HTTP ${HTTP_CODE})"
  echo ""
  echo "Response body:"
  echo "$BODY"
  echo ""
  echo "Common causes:"
  echo "  - HTTP 401/403: Invalid or expired PAT token"
  echo "  - HTTP 404: Incorrect MCP Server URL (check database/schema/server name)"
  echo "  - Connection refused/timeout: Network policy blocking Mistral IPs"
  exit 1
fi

echo ""

# ---------------------------------------------------------------------------
# Test 2: Invoke the agent tool with a simple question
# ---------------------------------------------------------------------------

echo "--- Test 2: Invoking agent tool ---"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${MCP_URL}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authorization: Bearer ${PAT_TOKEN}" \
  -H "X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN" \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"shipping-logistics-agent",
      "arguments":{"text":"How many shipments are currently in transit?"}
    }
  }')

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "SUCCESS (HTTP 200)"
  echo ""
  echo "The agent tool was invoked successfully and returned a response."
  echo "(The quality of the answer depends on whether data is loaded in the tables.)"
  echo ""
  echo "If you see an answer about shipments, connectivity is fully working."
  echo "If the agent says 'no data found', verify that load_sample_data.sql has been run."
else
  echo "FAILED (HTTP ${HTTP_CODE})"
  echo ""
  echo "Response: $BODY"
fi

echo ""
echo "============================================="
echo "Connectivity test complete."
echo "============================================="
