#!/bin/bash
# Copyright 2026 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


##############################################################################
# Grid Reliability & Predictive Maintenance - Cleanup Script
##############################################################################
# This script removes the deployed platform from Snowflake
# WARNING: This will delete all data and objects!
##############################################################################

set -e

# Disable exit on error for cleanup section (some objects may not exist)
cleanup_with_status() {
    set +e
    "$@"
    local exit_code=$?
    set -e
    return $exit_code
}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default values
CONNECTION="default"
DATABASE="UTILITIES_GRID_RELIABILITY"
WAREHOUSE="GRID_RELIABILITY_WH"
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--connection)
            CONNECTION="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --prefix)
            PREFIX="$2"
            DATABASE="${PREFIX}_${DATABASE}"
            WAREHOUSE="${PREFIX}_${WAREHOUSE}"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --connection NAME  Use specific connection (default: default)"
            echo "  --prefix PREFIX        Match prefix used during deployment"
            echo "  --force                Skip confirmation prompt"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                     # Clean with confirmation"
            echo "  $0 --force             # Clean without confirmation"
            echo "  $0 --prefix DEV        # Clean DEV deployment"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check for SQL command
if command -v snow &> /dev/null; then
    SQL_CMD="snow sql"
elif command -v snowsql &> /dev/null; then
    SQL_CMD="snowsql"
else
    echo -e "${RED}✗ Error: Neither 'snow' nor 'snowsql' command found${NC}"
    exit 1
fi

echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║              ⚠️  WARNING: CLEANUP OPERATION                    ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}This will DELETE the following:${NC}"
echo -e "  • ${RED}Intelligence Agent${NC}: Grid Reliability Intelligence Agent"
echo -e "  • ${RED}Cortex Search Services${NC}: 3 search services for documents"
echo -e "  • ${RED}Semantic View${NC}: Grid Reliability Analytics"
echo -e "  • ${RED}Database${NC}: ${DATABASE} (all schemas, tables, views, stages)"
echo -e "  • ${RED}Warehouse${NC}: ${WAREHOUSE}"
echo -e "  • ${RED}Roles${NC}: GRID_ADMIN, GRID_DATA_ENGINEER, GRID_ML_ENGINEER, GRID_ANALYST, GRID_OPERATOR"
echo -e "  • ${RED}All data${NC}: Asset data, sensor readings, maintenance logs, predictions"
echo ""

if [ "$FORCE" = false ]; then
    read -p "Are you sure you want to continue? (type 'YES' or 'yes' to confirm): " CONFIRM
    # Convert to uppercase for case-insensitive comparison
    CONFIRM_UPPER=$(echo "$CONFIRM" | tr '[:lower:]' '[:upper:]')
    if [ "$CONFIRM_UPPER" != "YES" ]; then
        echo -e "${YELLOW}Cleanup cancelled${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${BLUE}Starting cleanup...${NC}"
echo ""

# Execute cleanup
CLEANUP_SQL="
-- ============================================================================
-- CLEANUP ORDER: Drop dependent objects first, then parent objects
-- ============================================================================

-- Note: Agent removal from Intelligence object handled separately below

-- 2. Drop Intelligence Agent (depends on Cortex Search Services and Semantic View)
USE DATABASE ${DATABASE};
USE SCHEMA ANALYTICS;
DROP AGENT IF EXISTS \"Grid Reliability Intelligence Agent\";

-- 3. Drop Cortex Search Services (in UNSTRUCTURED schema)
USE SCHEMA UNSTRUCTURED;
DROP CORTEX SEARCH SERVICE IF EXISTS TECHNICAL_MANUAL_SEARCH;
DROP CORTEX SEARCH SERVICE IF EXISTS MAINTENANCE_LOG_SEARCH;
DROP CORTEX SEARCH SERVICE IF EXISTS DOCUMENT_SEARCH_SERVICE;

-- 4. Drop Semantic View (in ANALYTICS schema)
USE SCHEMA ANALYTICS;
DROP SEMANTIC VIEW IF EXISTS GRID_RELIABILITY_ANALYTICS;

-- 5. Drop Database (this drops all schemas, tables, views, stages, file formats)
DROP DATABASE IF EXISTS ${DATABASE};

-- 6. Drop Warehouse
DROP WAREHOUSE IF EXISTS ${WAREHOUSE};

-- 7. Drop Roles (these are account-level objects)
DROP ROLE IF EXISTS GRID_OPERATOR;
DROP ROLE IF EXISTS GRID_ANALYST;
DROP ROLE IF EXISTS GRID_ML_ENGINEER;
DROP ROLE IF EXISTS GRID_DATA_ENGINEER;
DROP ROLE IF EXISTS GRID_ADMIN;
"

echo -e "${YELLOW}▶ Unregistering Agent from Intelligence UI...${NC}"
# Remove agent from Intelligence object first (may fail if not registered, that's OK)
if [ "$SQL_CMD" = "snow sql" ]; then
    snow sql -c "$CONNECTION" -q "ALTER SNOWFLAKE INTELLIGENCE IDENTIFIER('SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT') REMOVE AGENT IDENTIFIER('UTILITIES_GRID_RELIABILITY.ANALYTICS.\"Grid Reliability Intelligence Agent\"');" --enable-templating NONE 2>/dev/null || true
else
    snowsql -c "$CONNECTION" -q "ALTER SNOWFLAKE INTELLIGENCE IDENTIFIER('SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT') REMOVE AGENT IDENTIFIER('UTILITIES_GRID_RELIABILITY.ANALYTICS.\"Grid Reliability Intelligence Agent\"');" 2>/dev/null || true
fi

echo -e "${YELLOW}▶ Removing Intelligence Agent...${NC}"
echo -e "${YELLOW}▶ Removing Cortex Search Services...${NC}"
echo -e "${YELLOW}▶ Removing Semantic Views...${NC}"
echo -e "${YELLOW}▶ Removing Database and all data...${NC}"
echo -e "${YELLOW}▶ Removing Warehouse...${NC}"
echo -e "${YELLOW}▶ Removing Custom Roles...${NC}"
echo ""

if [ "$SQL_CMD" = "snow sql" ]; then
    cleanup_with_status snow sql -c "$CONNECTION" -q "$CLEANUP_SQL" --enable-templating NONE
else
    cleanup_with_status sh -c "echo \"$CLEANUP_SQL\" | snowsql -c \"$CONNECTION\""
fi

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✓ CLEANUP COMPLETED                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Successfully removed:${NC}"
echo -e "  ✓ Intelligence Agent and Cortex Search Services"
echo -e "  ✓ Semantic Views and Analytics Objects"
echo -e "  ✓ Database with all schemas, tables, and data"
echo -e "  ✓ Warehouse and compute resources"
echo -e "  ✓ Custom roles and permissions"
echo ""
echo -e "${BLUE}Your Snowflake account is now clean${NC}"
echo ""
echo -e "To redeploy: ${YELLOW}./deploy.sh -c ${CONNECTION}${NC}"
echo ""

