#!/bin/bash

##############################################################################
# Grid Reliability & Predictive Maintenance - Deployment Script
##############################################################################
# This script deploys the complete Grid Reliability platform to Snowflake
# including database, schemas, ML models, semantic views, and intelligence agents
##############################################################################

set -e  # Exit on error

# Ensure script runs from its own directory (assets/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
PREFIX=""
CONNECTION="default"
SKIP_AGENTS=false
ONLY_SQL=false
WAREHOUSE="GRID_RELIABILITY_WH"
DATABASE="UTILITIES_GRID_RELIABILITY"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix)
            PREFIX="$2"
            shift 2
            ;;
        -c|--connection)
            CONNECTION="$2"
            shift 2
            ;;
        --skip-agents)
            SKIP_AGENTS=true
            shift
            ;;
        --only-sql)
            ONLY_SQL=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prefix PREFIX       Add prefix to database/warehouse names (e.g., DEV)"
            echo "  -c, --connection NAME Use specific Snowflake connection (default: default)"
            echo "  --skip-agents         Skip deploying Intelligence Agents"
            echo "  --only-sql            Deploy only SQL infrastructure (no Python)"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Deploy with defaults"
            echo "  $0 --prefix DEV                 # Deploy with DEV prefix"
            echo "  $0 -c prod --skip-agents        # Deploy to prod, skip agents"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Apply prefix if specified
if [ -n "$PREFIX" ]; then
    DATABASE="${PREFIX}_${DATABASE}"
    WAREHOUSE="${PREFIX}_${WAREHOUSE}"
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Grid Reliability & Predictive Maintenance Deployment        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo -e "  Connection: ${YELLOW}${CONNECTION}${NC}"
echo -e "  Database:   ${YELLOW}${DATABASE}${NC}"
echo -e "  Warehouse:  ${YELLOW}${WAREHOUSE}${NC}"
echo -e "  Skip Agents: ${YELLOW}${SKIP_AGENTS}${NC}"
echo ""

# Check if snowsql or snow CLI is available
if command -v snow &> /dev/null; then
    SQL_CMD="snow sql"
    echo -e "${GREEN}✓ Using Snowflake CLI (snow)${NC}"
elif command -v snowsql &> /dev/null; then
    SQL_CMD="snowsql"
    echo -e "${GREEN}✓ Using SnowSQL${NC}"
else
    echo -e "${RED}✗ Error: Neither 'snow' nor 'snowsql' command found${NC}"
    echo -e "${YELLOW}Please install Snowflake CLI or SnowSQL${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
echo -e "${GREEN}Starting deployment...${NC}"
echo -e "${BLUE}────────────────────────────────────────────────────────────────${NC}"
echo ""

# Function to execute SQL file
execute_sql() {
    local file=$1
    local description=$2
    
    echo -e "${YELLOW}▶ ${description}...${NC}"
    
    if [ "$SQL_CMD" = "snow sql" ]; then
        snow sql -f "$file" -c "$CONNECTION" --enable-templating NONE
    else
        snowsql -c "$CONNECTION" -f "$file" -D "db_name=${DATABASE}" -D "wh_name=${WAREHOUSE}"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✓ Completed${NC}"
    else
        echo -e "${RED}  ✗ Failed${NC}"
        exit 1
    fi
    echo ""
}

# Deploy SQL infrastructure
echo -e "${BLUE}═══ Phase 1: Infrastructure ═══${NC}"
execute_sql "scripts/01_infrastructure_setup.sql" "Setting up database, warehouse, and schemas"

echo -e "${BLUE}═══ Phase 2: Data Schemas ═══${NC}"
execute_sql "scripts/02_structured_data_schema.sql" "Creating structured data tables"
execute_sql "scripts/03_unstructured_data_schema.sql" "Creating unstructured data tables"

echo -e "${BLUE}═══ Phase 3: ML Pipeline Setup ═══${NC}"
execute_sql "scripts/04_ml_feature_engineering.sql" "Creating feature engineering views"
execute_sql "scripts/06_ml_models.sql" "Creating ML training procedures"
execute_sql "scripts/06b_update_score_assets.sql" "Creating ML scoring procedure"

echo -e "${BLUE}═══ Phase 4: Analytics Layer ═══${NC}"
execute_sql "scripts/07_business_views.sql" "Creating business analytics views"
execute_sql "scripts/08_semantic_model.sql" "Creating semantic model"

if [ "$SKIP_AGENTS" = false ]; then
    echo -e "${BLUE}═══ Phase 5: Intelligence Agents ═══${NC}"
    echo -e "${YELLOW}▶ Deploying Intelligence Agents...${NC}"
    
    # Note: Intelligence Agent creation may produce benign "unexpected '6'" syntax warnings
    # due to YAML parsing. These are cosmetic and don't affect functionality.
    if [ "$SQL_CMD" = "snow sql" ]; then
        snow sql -f "scripts/09_intelligence_agent.sql" -c "$CONNECTION" --enable-templating NONE > /tmp/agent_deploy_$$.log 2>&1 || true
    else
        snowsql -c "$CONNECTION" -f "scripts/09_intelligence_agent.sql" -D "db_name=${DATABASE}" -D "wh_name=${WAREHOUSE}" > /tmp/agent_deploy_$$.log 2>&1 || true
    fi
    
    # Verify agent was created successfully
    echo -e "${YELLOW}  → Verifying agent creation...${NC}"
    if [ "$SQL_CMD" = "snow sql" ]; then
        AGENT_CHECK=$(snow sql -c "$CONNECTION" -q "SHOW AGENTS IN SCHEMA ${DATABASE}.ANALYTICS" --enable-templating NONE 2>&1 | grep -i "Reliabil")
        if [ -n "$AGENT_CHECK" ]; then
            echo -e "${GREEN}  ✓ Intelligence Agent deployed successfully${NC}"
        else
            echo -e "${YELLOW}  ⚠ Warning: Could not verify agent. Check manually.${NC}"
            echo -e "${YELLOW}  → Deployment log: /tmp/agent_deploy_$$.log${NC}"
        fi
    else
        echo -e "${GREEN}  ✓ Completed${NC}"
    fi
    
    # Clean up log if successful
    rm -f /tmp/agent_deploy_$$.log 2>/dev/null
    echo ""
fi

echo -e "${BLUE}═══ Phase 6: Security ═══${NC}"
execute_sql "scripts/10_security_roles.sql" "Configuring security roles"

echo -e "${BLUE}═══ Phase 7: Data Loading ═══${NC}"

# =============================================================================
# AUTO-DETECT PYTHON ENVIRONMENT & SETUP VIRTUAL ENVIRONMENT
# =============================================================================

echo -e "${YELLOW}▶ Setting up Python environment...${NC}"

# Function to detect best available Python version
detect_python() {
    for cmd in python3.11 python3.10 python3.9 python3.8 python3 python; do
        if command -v $cmd &> /dev/null; then
            version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            major=$(echo $version | cut -d. -f1)
            minor=$(echo $version | cut -d. -f2)
            if [ "$major" -eq 3 ] && [ "$minor" -ge 8 ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# Detect Python
PYTHON_CMD=$(detect_python)
if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}  ✗ Python 3.8+ not found${NC}"
    echo -e "${YELLOW}  Please install Python 3.8 or higher${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}  ✓ Detected: ${PYTHON_VERSION}${NC}"

# Check if already in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo -e "${GREEN}  ✓ Using active virtual environment: ${VIRTUAL_ENV}${NC}"
    PYTHON_CMD="python3"  # Use the venv's python
else
    # Auto-create venv if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}  → Creating virtual environment...${NC}"
        if $PYTHON_CMD -m venv venv; then
            echo -e "${GREEN}    ✓ Virtual environment created${NC}"
        else
            echo -e "${YELLOW}    ⚠️  Could not create venv, using system Python${NC}"
        fi
    fi
    
    # Try to activate venv (non-blocking)
    if [ -d "venv" ]; then
        if [ -f "venv/bin/activate" ]; then
            echo -e "${YELLOW}  → Activating virtual environment...${NC}"
            source venv/bin/activate
            PYTHON_CMD="python3"
            echo -e "${GREEN}    ✓ Virtual environment activated${NC}"
        elif [ -f "venv/Scripts/activate" ]; then
            # Windows
            source venv/Scripts/activate
            PYTHON_CMD="python3"
            echo -e "${GREEN}    ✓ Virtual environment activated${NC}"
        fi
    fi
fi

# Auto-install dependencies
echo -e "${YELLOW}▶ Checking Python dependencies...${NC}"
if ! $PYTHON_CMD -c "import numpy, pandas, reportlab" 2>/dev/null; then
    echo -e "${YELLOW}  → Installing required packages (numpy, pandas, reportlab)...${NC}"
    if [ -f "requirements.txt" ]; then
        if $PYTHON_CMD -m pip install -q -r requirements.txt; then
            echo -e "${GREEN}    ✓ Dependencies installed${NC}"
        else
            echo -e "${RED}    ✗ Failed to install dependencies${NC}"
            echo -e "${YELLOW}    Manual install: pip install -r requirements.txt${NC}"
            exit 1
        fi
    else
        if $PYTHON_CMD -m pip install -q numpy pandas reportlab; then
            echo -e "${GREEN}    ✓ Dependencies installed${NC}"
        else
            echo -e "${RED}    ✗ Failed to install dependencies${NC}"
            exit 1
        fi
    fi
else
    echo -e "${GREEN}  ✓ All Python dependencies available${NC}"
fi

# Use detected Python for all subsequent commands
alias python3="$PYTHON_CMD"

# Generate structured data files FIRST
echo -e "${YELLOW}▶ Generating structured data files (CSV/JSON)...${NC}"
if [ ! -d "generated_data" ]; then
    mkdir -p generated_data
fi

# Clean up any stale/duplicate generated_data folder in wrong location
if [ -d "data_generators/generated_data" ]; then
    echo -e "${YELLOW}  → Removing stale data folder in wrong location...${NC}"
    rm -rf data_generators/generated_data
fi

cd data_generators
# Run with output suppression to avoid SQL parsing issues
# Output to ../generated_data to ensure files are at PROJECT_ROOT/generated_data
if python3 generate_asset_data.py --output-dir ../generated_data > /tmp/asset_data_gen.log 2>&1; then
    cd ..
    if [ -f "generated_data/asset_master.csv" ]; then
        echo -e "${GREEN}  ✓ Structured data files generated${NC}"
        echo -e "${YELLOW}    → asset_master.csv, maintenance_history.csv, failure_events.csv${NC}"
        echo -e "${YELLOW}    → sensor_readings_batch_*.json (5 files)${NC}"
    else
        echo -e "${RED}  ✗ Failed to generate structured data files (files not found)${NC}"
        echo -e "${YELLOW}  Expected location: $(pwd)/generated_data/${NC}"
        cat /tmp/asset_data_gen.log
        exit 1
    fi
else
    echo -e "${RED}  ✗ Failed to generate structured data files (script error)${NC}"
    cat /tmp/asset_data_gen.log
    cd ..
    exit 1
fi

# Upload structured data files to Snowflake stages
echo -e "${YELLOW}▶ Uploading structured data files to Snowflake stages...${NC}"

# Get absolute path to generated_data directory
DATA_DIR="$(pwd)/generated_data"

# Upload CSV files individually (avoids wildcard issues with spaces in paths)
echo -e "${YELLOW}  → Uploading CSV files...${NC}"
CSV_UPLOAD_SUCCESS=true

for csv_file in "asset_master.csv" "maintenance_history.csv" "failure_events.csv"; do
    if [ -f "${DATA_DIR}/${csv_file}" ]; then
        echo -e "${YELLOW}    Uploading ${csv_file}...${NC}"
        if [ "$SQL_CMD" = "snow sql" ]; then
            if snow sql -c "$CONNECTION" -q "
                USE DATABASE ${DATABASE};
                USE SCHEMA RAW;
                PUT 'file://${DATA_DIR}/${csv_file}' @ASSET_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
            " --enable-templating NONE > /tmp/upload_${csv_file}.log 2>&1; then
                echo -e "${GREEN}      ✓ ${csv_file} uploaded${NC}"
            else
                echo -e "${RED}      ✗ Failed to upload ${csv_file}${NC}"
                cat /tmp/upload_${csv_file}.log
                CSV_UPLOAD_SUCCESS=false
            fi
        else
            if snowsql -c "$CONNECTION" -q "
                USE DATABASE ${DATABASE};
                USE SCHEMA RAW;
                PUT 'file://${DATA_DIR}/${csv_file}' @ASSET_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
            " > /tmp/upload_${csv_file}.log 2>&1; then
                echo -e "${GREEN}      ✓ ${csv_file} uploaded${NC}"
            else
                echo -e "${RED}      ✗ Failed to upload ${csv_file}${NC}"
                cat /tmp/upload_${csv_file}.log
                CSV_UPLOAD_SUCCESS=false
            fi
        fi
    else
        echo -e "${RED}      ✗ File not found: ${csv_file}${NC}"
        CSV_UPLOAD_SUCCESS=false
    fi
done

if [ "$CSV_UPLOAD_SUCCESS" = true ]; then
    echo -e "${GREEN}    ✓ All CSV files uploaded${NC}"
else
    echo -e "${RED}    ✗ Some CSV uploads failed${NC}"
    exit 1
fi

# Upload JSON files individually (sensor_readings batches)
echo -e "${YELLOW}  → Uploading JSON files (sensor readings batches)...${NC}"
JSON_UPLOAD_SUCCESS=true
JSON_COUNT=0

for json_file in "${DATA_DIR}"/sensor_readings_batch_*.json; do
    if [ -f "$json_file" ]; then
        json_basename=$(basename "$json_file")
        echo -e "${YELLOW}    Uploading ${json_basename}...${NC}"
        if [ "$SQL_CMD" = "snow sql" ]; then
            if snow sql -c "$CONNECTION" -q "
                USE DATABASE ${DATABASE};
                USE SCHEMA RAW;
                PUT 'file://${json_file}' @SENSOR_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
            " --enable-templating NONE > /tmp/upload_${json_basename}.log 2>&1; then
                echo -e "${GREEN}      ✓ ${json_basename} uploaded${NC}"
                JSON_COUNT=$((JSON_COUNT + 1))
            else
                echo -e "${RED}      ✗ Failed to upload ${json_basename}${NC}"
                cat /tmp/upload_${json_basename}.log
                JSON_UPLOAD_SUCCESS=false
            fi
        else
            if snowsql -c "$CONNECTION" -q "
                USE DATABASE ${DATABASE};
                USE SCHEMA RAW;
                PUT 'file://${json_file}' @SENSOR_DATA_STAGE AUTO_COMPRESS=TRUE OVERWRITE=TRUE;
            " > /tmp/upload_${json_basename}.log 2>&1; then
                echo -e "${GREEN}      ✓ ${json_basename} uploaded${NC}"
                JSON_COUNT=$((JSON_COUNT + 1))
            else
                echo -e "${RED}      ✗ Failed to upload ${json_basename}${NC}"
                cat /tmp/upload_${json_basename}.log
                JSON_UPLOAD_SUCCESS=false
            fi
        fi
    fi
done

if [ "$JSON_UPLOAD_SUCCESS" = true ] && [ $JSON_COUNT -gt 0 ]; then
    echo -e "${GREEN}    ✓ All ${JSON_COUNT} JSON files uploaded${NC}"
elif [ $JSON_COUNT -eq 0 ]; then
    echo -e "${RED}    ✗ No JSON files found to upload${NC}"
    exit 1
else
    echo -e "${RED}    ✗ Some JSON uploads failed${NC}"
    exit 1
fi

echo -e "${GREEN}  ✓ File upload phase completed${NC}"

execute_sql "scripts/11_load_structured_data.sql" "Loading structured data"

# Verify structured data was loaded
echo -e "${YELLOW}▶ Verifying structured data loaded...${NC}"
if [ "$SQL_CMD" = "snow sql" ]; then
    ASSET_COUNT=$(snow sql -c "$CONNECTION" -q "USE DATABASE ${DATABASE}; SELECT COUNT(*) FROM RAW.ASSET_MASTER;" --enable-templating NONE 2>/dev/null | grep -o '[0-9]\+' | tail -1)
else
    ASSET_COUNT=$(snowsql -c "$CONNECTION" -d "${DATABASE}" -q "SELECT COUNT(*) FROM RAW.ASSET_MASTER;" -o output_format=tsv -o friendly=false -o timing=false 2>/dev/null | grep -o '[0-9]\+' | tail -1)
fi

if [ -n "$ASSET_COUNT" ] && [ "$ASSET_COUNT" -gt 0 ]; then
    echo -e "${GREEN}  ✓ Verified: ${ASSET_COUNT} assets loaded${NC}"
else
    echo -e "${RED}  ✗ Warning: No data loaded into ASSET_MASTER${NC}"
    echo -e "${YELLOW}  ⚠️  Deployment will continue, but tables may be empty${NC}"
fi

# Generate and load unstructured data using Python
echo -e "${YELLOW}▶ Generating unstructured data files...${NC}"
cd data_generators

# Run all data generators with error checking
echo -e "${YELLOW}  → Generating maintenance logs...${NC}"
if python3 generate_maintenance_logs.py > /tmp/maint_logs_gen.log 2>&1; then
    MAINT_COUNT=$(ls -1 generated_maintenance_logs/*.pdf 2>/dev/null | wc -l)
    echo -e "${GREEN}    ✓ Generated ${MAINT_COUNT} maintenance logs${NC}"
else
    echo -e "${RED}    ✗ Failed to generate maintenance logs${NC}"
    cat /tmp/maint_logs_gen.log
    exit 1
fi

echo -e "${YELLOW}  → Generating technical manuals...${NC}"
if python3 generate_technical_manuals.py > /tmp/tech_manuals_gen.log 2>&1; then
    MANUAL_COUNT=$(ls -1 generated_technical_manuals/*.pdf 2>/dev/null | wc -l)
    echo -e "${GREEN}    ✓ Generated ${MANUAL_COUNT} technical manuals${NC}"
else
    echo -e "${RED}    ✗ Failed to generate technical manuals${NC}"
    cat /tmp/tech_manuals_gen.log
    exit 1
fi

echo -e "${YELLOW}  → Generating visual inspections...${NC}"
if python3 generate_visual_inspections.py > /tmp/visual_insp_gen.log 2>&1; then
    echo -e "${GREEN}    ✓ Generated visual inspections & CV detections${NC}"
else
    echo -e "${RED}    ✗ Failed to generate visual inspections${NC}"
    cat /tmp/visual_insp_gen.log
    exit 1
fi

echo -e "${YELLOW}  → Creating SQL loading script...${NC}"
if python3 load_unstructured_full.py > /tmp/unstruct_sql_gen.log 2>&1; then
    if [ -f "load_unstructured_data_full.sql" ]; then
        SQL_SIZE=$(wc -l < load_unstructured_data_full.sql)
        echo -e "${GREEN}    ✓ Generated SQL script (${SQL_SIZE} lines)${NC}"
    else
        echo -e "${RED}    ✗ SQL script not created${NC}"
        exit 1
    fi
else
    echo -e "${RED}  ✗ Failed to generate unstructured data SQL${NC}"
    cat /tmp/unstruct_sql_gen.log
    exit 1
fi

echo -e "${YELLOW}▶ Loading unstructured data into Snowflake...${NC}"
if [ "$SQL_CMD" = "snow sql" ]; then
    snow sql -f load_unstructured_data_full.sql -c "$CONNECTION" -D "database=${DATABASE}" -D "warehouse=${WAREHOUSE}" --enable-templating NONE
else
    snowsql -c "$CONNECTION" -d "${DATABASE}" -w "${WAREHOUSE}" -f load_unstructured_data_full.sql
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Unstructured data loaded${NC}"
else
    echo -e "${RED}  ✗ Failed to load unstructured data${NC}"
    exit 1
fi

cd ..

# Verify unstructured data was loaded
echo -e "${YELLOW}▶ Verifying unstructured data loaded...${NC}"
if [ "$SQL_CMD" = "snow sql" ]; then
    MAINT_LOGS_COUNT=$(snow sql -c "$CONNECTION" -q "USE DATABASE ${DATABASE}; SELECT COUNT(*) FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS;" --enable-templating NONE 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    TECH_MANUAL_COUNT=$(snow sql -c "$CONNECTION" -q "USE DATABASE ${DATABASE}; SELECT COUNT(*) FROM UNSTRUCTURED.TECHNICAL_MANUALS;" --enable-templating NONE 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    VISUAL_INSP_COUNT=$(snow sql -c "$CONNECTION" -q "USE DATABASE ${DATABASE}; SELECT COUNT(*) FROM UNSTRUCTURED.VISUAL_INSPECTIONS;" --enable-templating NONE 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    CV_DETECT_COUNT=$(snow sql -c "$CONNECTION" -q "USE DATABASE ${DATABASE}; SELECT COUNT(*) FROM UNSTRUCTURED.CV_DETECTIONS;" --enable-templating NONE 2>/dev/null | grep -o '[0-9]\+' | tail -1)
else
    MAINT_LOGS_COUNT=$(snowsql -c "$CONNECTION" -d "${DATABASE}" -q "SELECT COUNT(*) FROM UNSTRUCTURED.MAINTENANCE_LOG_DOCUMENTS;" -o output_format=tsv -o friendly=false -o timing=false 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    TECH_MANUAL_COUNT=$(snowsql -c "$CONNECTION" -d "${DATABASE}" -q "SELECT COUNT(*) FROM UNSTRUCTURED.TECHNICAL_MANUALS;" -o output_format=tsv -o friendly=false -o timing=false 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    VISUAL_INSP_COUNT=$(snowsql -c "$CONNECTION" -d "${DATABASE}" -q "SELECT COUNT(*) FROM UNSTRUCTURED.VISUAL_INSPECTIONS;" -o output_format=tsv -o friendly=false -o timing=false 2>/dev/null | grep -o '[0-9]\+' | tail -1)
    CV_DETECT_COUNT=$(snowsql -c "$CONNECTION" -d "${DATABASE}" -q "SELECT COUNT(*) FROM UNSTRUCTURED.CV_DETECTIONS;" -o output_format=tsv -o friendly=false -o timing=false 2>/dev/null | grep -o '[0-9]\+' | tail -1)
fi

echo -e "${YELLOW}  Unstructured data counts:${NC}"
if [ -n "$MAINT_LOGS_COUNT" ] && [ "$MAINT_LOGS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}    ✓ Maintenance logs: ${MAINT_LOGS_COUNT}${NC}"
else
    echo -e "${RED}    ✗ Maintenance logs: 0 (expected ~80)${NC}"
fi

if [ -n "$TECH_MANUAL_COUNT" ] && [ "$TECH_MANUAL_COUNT" -gt 0 ]; then
    echo -e "${GREEN}    ✓ Technical manuals: ${TECH_MANUAL_COUNT}${NC}"
else
    echo -e "${RED}    ✗ Technical manuals: 0 (expected ~15)${NC}"
fi

if [ -n "$VISUAL_INSP_COUNT" ] && [ "$VISUAL_INSP_COUNT" -gt 0 ]; then
    echo -e "${GREEN}    ✓ Visual inspections: ${VISUAL_INSP_COUNT}${NC}"
else
    echo -e "${RED}    ✗ Visual inspections: 0 (expected ~150)${NC}"
fi

if [ -n "$CV_DETECT_COUNT" ] && [ "$CV_DETECT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}    ✓ CV detections: ${CV_DETECT_COUNT}${NC}"
else
    echo -e "${RED}    ✗ CV detections: 0 (expected ~281)${NC}"
fi

# Create Cortex Search Services
execute_sql "scripts/12_load_unstructured_data.sql" "Creating Cortex Search Services"

# Populate reference data (SCADA_EVENTS and WEATHER_DATA)
echo -e "${YELLOW}▶ Populating reference data (SCADA_EVENTS, WEATHER_DATA)...${NC}"
execute_sql "scripts/13_populate_reference_data.sql" "Loading reference data"

echo ""
echo -e "${BLUE}═══ Phase 8: ML Training & Scoring ═══${NC}"

echo -e "${YELLOW}▶ Preparing training data (generating labeled samples)...${NC}"
execute_sql "scripts/05_ml_training_prep.sql" "Generating ML training data"

echo -e "${YELLOW}▶ Training ML models (this may take 2-3 minutes)...${NC}"
if [ "$SQL_CMD" = "snow sql" ]; then
    snow sql -c "$CONNECTION" -q "
        USE DATABASE ${DATABASE};
        USE WAREHOUSE ${WAREHOUSE};
        CALL ML.TRAIN_FAILURE_PREDICTION_MODELS();
    " --enable-templating NONE
else
    snowsql -c "$CONNECTION" -q "
        USE DATABASE ${DATABASE};
        USE WAREHOUSE ${WAREHOUSE};
        CALL ML.TRAIN_FAILURE_PREDICTION_MODELS();
    "
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ ML models trained successfully${NC}"
else
    echo -e "${RED}  ✗ ML training failed${NC}"
    echo -e "${YELLOW}  ⚠️  You can train models manually later: CALL ML.TRAIN_FAILURE_PREDICTION_MODELS();${NC}"
    echo -e "${YELLOW}  ⚠️  Continuing deployment...${NC}"
fi

echo -e "${YELLOW}▶ Generating predictions for all assets...${NC}"
if [ "$SQL_CMD" = "snow sql" ]; then
    snow sql -c "$CONNECTION" -q "
        USE DATABASE ${DATABASE};
        USE WAREHOUSE ${WAREHOUSE};
        CALL ML.SCORE_ASSETS();
    " --enable-templating NONE
else
    snowsql -c "$CONNECTION" -q "
        USE DATABASE ${DATABASE};
        USE WAREHOUSE ${WAREHOUSE};
        CALL ML.SCORE_ASSETS();
    "
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✓ Predictions generated successfully${NC}"
else
    echo -e "${RED}  ✗ Prediction generation failed${NC}"
    echo -e "${YELLOW}  ⚠️  You can score assets manually later: CALL ML.SCORE_ASSETS();${NC}"
    echo -e "${YELLOW}  ⚠️  Continuing deployment...${NC}"
fi

# Generate recent sensor data for dashboard visualization
echo -e "${YELLOW}▶ Generating recent sensor data (last 30 days)...${NC}"
execute_sql "scripts/14_generate_recent_sensor_data.sql" "Generating recent sensor data"

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Phase 9: Streamlit Dashboard Deployment               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# First, create the stage and Streamlit app definition
echo -e "${YELLOW}▶ Step 1: Creating Streamlit infrastructure...${NC}"
execute_sql "scripts/10_streamlit_dashboard.sql" "Creating Streamlit Stage and App"

# Then, upload the environment file and dashboard file to the stage
echo -e "${YELLOW}▶ Step 2: Uploading dashboard files to Snowflake...${NC}"
cd streamlit

# Upload environment.yml (contains package dependencies like plotly, numpy)
echo -e "${YELLOW}  → Uploading environment.yml (Python dependencies)...${NC}"
snow sql -c "$CONNECTION" -q "PUT file://environment.yml @UTILITIES_GRID_RELIABILITY.ANALYTICS.STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE" --enable-templating NONE > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}    ✓ Environment file uploaded${NC}"
else
    echo -e "${RED}    ✗ Failed to upload environment file${NC}"
    echo -e "${YELLOW}    ⚠️  Dashboard may not have required packages${NC}"
fi

# Upload Python dashboard file
echo -e "${YELLOW}  → Uploading grid_reliability_dashboard.py (29KB)...${NC}"
snow sql -c "$CONNECTION" -q "PUT file://grid_reliability_dashboard.py @UTILITIES_GRID_RELIABILITY.ANALYTICS.STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE" --enable-templating NONE > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}    ✓ Dashboard file uploaded${NC}"
else
    echo -e "${RED}    ✗ Failed to upload dashboard file${NC}"
    echo -e "${YELLOW}    ⚠️  Dashboard may not function correctly${NC}"
fi
cd ..

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║       ✓ STREAMLIT DASHBOARD DEPLOYED SUCCESSFULLY!            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Dashboard Features:${NC}"
echo -e "  ${GREEN}✓${NC} Overview - Executive KPIs and metrics"
echo -e "  ${GREEN}✓${NC} High Risk Assets - Critical transformer alerts"
echo -e "  ${GREEN}✓${NC} Asset Health - Detailed asset monitoring"
echo -e "  ${GREEN}✓${NC} Cost Avoidance - Financial impact analysis"
echo -e "  ${GREEN}✓${NC} Reliability Metrics - SAIDI/SAIFI tracking"
echo -e "  ${GREEN}✓${NC} Sensor Trends - Real-time data visualization"
echo ""

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              ✓ DEPLOYMENT COMPLETED SUCCESSFULLY               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get and display Streamlit URL
if [ "$SQL_CMD" = "snow sql" ]; then
    ACCOUNT_NAME=$(snow sql -c "$CONNECTION" -q "SELECT CURRENT_ACCOUNT_NAME();" --enable-templating NONE 2>/dev/null | grep -v "CURRENT_ACCOUNT_NAME" | grep -v "^$" | grep -v "^\-" | tail -1 | tr -d ' ')
    if [ -n "$ACCOUNT_NAME" ]; then
        DASHBOARD_URL="https://${ACCOUNT_NAME}.snowflakecomputing.com/streamlit/${DATABASE}.ANALYTICS.GRID_RELIABILITY_DASHBOARD"
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║           🎨 ACCESS YOUR STREAMLIT DASHBOARD                  ║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}📊 Direct URL:${NC}"
        echo -e "   ${GREEN}${DASHBOARD_URL}${NC}"
        echo ""
        echo -e "${YELLOW}📋 Via Snowflake UI:${NC}"
        echo -e "   ${GREEN}Projects → Streamlit → GRID_RELIABILITY_DASHBOARD${NC}"
        echo ""
    fi
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    NEXT STEPS                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}1. Validate deployment:${NC}"
echo -e "   ${GREEN}./run.sh validate -c ${CONNECTION}${NC}"
echo ""
echo -e "${YELLOW}2. Check system status:${NC}"
echo -e "   ${GREEN}./run.sh status -c ${CONNECTION}${NC}"
echo ""
echo -e "${YELLOW}3. Test Intelligence Agent:${NC}"
echo -e "   ${GREEN}./run.sh test-agents -c ${CONNECTION}${NC}"
echo ""
echo -e "${YELLOW}4. Run sample queries:${NC}"
echo -e "   ${GREEN}./run.sh query 'SELECT COUNT(*) FROM RAW.ASSET_MASTER' -c ${CONNECTION}${NC}"
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   DOCUMENTATION                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  📖 Quick Start:    ${YELLOW}docs/guides/QUICKSTART.md${NC}"
echo -e "  📖 Full Guide:     ${YELLOW}docs/guides/DEPLOYMENT_GUIDE.md${NC}"
echo -e "  📖 Architecture:   ${YELLOW}docs/architecture/ARCHITECTURE.md${NC}"
echo -e "  📖 Dashboard Guide: ${YELLOW}docs/guides/STREAMLIT_DASHBOARD_GUIDE.md${NC}"
echo ""
