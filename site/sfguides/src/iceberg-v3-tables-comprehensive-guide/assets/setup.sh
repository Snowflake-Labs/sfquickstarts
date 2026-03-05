#!/bin/bash
# Snowflake Iceberg V3 Comprehensive Guide - Setup Script
# This script creates all necessary Snowflake objects for the guide

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Iceberg V3 Comprehensive Guide Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check for config file - create from template if needed
if [ ! -f "config.env" ]; then
    if [ -f "config.env.template" ]; then
        echo -e "${YELLOW}config.env not found. Creating from template...${NC}"
        cp config.env.template config.env
        echo ""
        echo -e "${YELLOW}IMPORTANT: Please edit config.env with your values before continuing.${NC}"
        echo "At minimum, update:"
        echo "  - SNOWFLAKE_CONNECTION (your Snowflake CLI connection name)"
        echo "  - Storage provider settings (or set USE_EXISTING_VOLUME=true)"
        echo ""
        read -p "Open config.env in your editor now, then press Enter to continue... "
    else
        echo -e "${RED}Error: Neither config.env nor config.env.template found!${NC}"
        exit 1
    fi
fi

# Load configuration
source config.env

# Set default connection name if not specified
SNOWFLAKE_CONNECTION="${SNOWFLAKE_CONNECTION:-default}"

# Check if Snowflake CLI is installed
if ! command -v snow &> /dev/null; then
    echo -e "${RED}Error: Snowflake CLI not found!${NC}"
    echo ""
    echo "Please install Snowflake CLI first:"
    echo "  https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation"
    exit 1
fi

echo -e "${GREEN}Configuration loaded successfully${NC}"
echo "  Connection: $SNOWFLAKE_CONNECTION"
echo "  Database: $SNOWFLAKE_DATABASE"
echo "  Warehouse: $SNOWFLAKE_WAREHOUSE"
echo ""

# Test the connection
echo "Testing Snowflake CLI connection '$SNOWFLAKE_CONNECTION'..."
if ! snow connection test --connection "$SNOWFLAKE_CONNECTION" &> /dev/null; then
    echo -e "${YELLOW}Warning: Could not verify connection '$SNOWFLAKE_CONNECTION'.${NC}"
    echo "Make sure the connection is configured in your Snowflake CLI config."
    echo ""
    echo "To check your connections: snow connection list"
    echo "To add a connection: snow connection add --connection-name $SNOWFLAKE_CONNECTION"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}Connection verified!${NC}"
fi
echo ""

# Detect Snowflake edition to determine feature availability
echo "Detecting Snowflake edition..."
SNOWFLAKE_EDITION=$(snow sql --connection="$SNOWFLAKE_CONNECTION" --query="SELECT SYSTEM\$GET_EDITION()" --format=json 2>/dev/null | grep -o '"SYSTEM\$GET_EDITION()":"[^"]*"' | cut -d'"' -f4 || echo "UNKNOWN")

if [ -z "$SNOWFLAKE_EDITION" ] || [ "$SNOWFLAKE_EDITION" == "UNKNOWN" ]; then
    # Fallback: try without escaping
    SNOWFLAKE_EDITION=$(snow sql --connection="$SNOWFLAKE_CONNECTION" --query="SELECT CURRENT_VERSION()" --format=json 2>/dev/null | head -1)
    # If still can't detect, assume Enterprise
    SNOWFLAKE_EDITION="ENTERPRISE"
    echo -e "${YELLOW}Could not detect edition, assuming Enterprise features available${NC}"
else
    echo -e "${GREEN}Detected Snowflake edition: $SNOWFLAKE_EDITION${NC}"
fi

# Check if governance features are available (Enterprise+)
GOVERNANCE_AVAILABLE=true
case "$SNOWFLAKE_EDITION" in
    "STANDARD"|"standard"|"Standard")
        GOVERNANCE_AVAILABLE=false
        echo -e "${YELLOW}Standard Edition detected - masking policies and data quality features will be skipped${NC}"
        ;;
    *)
        echo "Enterprise/Business Critical features (masking, data quality) are available"
        ;;
esac
echo ""

# Create Python virtual environment for streaming
echo -e "${YELLOW}Step 1: Setting up Python environment...${NC}"
if [ ! -d "iceberg_v3_demo_venv" ]; then
    python3 -m venv iceberg_v3_demo_venv
fi
source iceberg_v3_demo_venv/bin/activate
pip install -q snowflake-connector-python snowflake-ingest python-dotenv faker requests

echo -e "${GREEN}Python environment ready${NC}"
echo ""

# Generate external volume SQL based on storage configuration
echo -e "${YELLOW}Step 2: Generating external volume configuration...${NC}"

generate_external_volume_sql() {
    if [ "$USE_EXISTING_VOLUME" == "true" ] && [ -n "$EXISTING_VOLUME_NAME" ]; then
        echo "-- Using existing external volume: $EXISTING_VOLUME_NAME"
        echo "-- ALTER DATABASE command will be added to database creation script"
        return
    fi
    
    case $STORAGE_PROVIDER in
        "S3")
            cat << EOF
-- Create External Volume for AWS S3
CREATE OR REPLACE EXTERNAL VOLUME FLEET_ICEBERG_VOL
  STORAGE_LOCATIONS = (
    (
      NAME = 'fleet_s3_storage'
      STORAGE_PROVIDER = 'S3'
      STORAGE_BASE_URL = 's3://${S3_BUCKET_NAME}/${S3_PATH}'
      STORAGE_AWS_ROLE_ARN = '${AWS_ROLE_ARN}'
EOF
            if [ "$S3_ENCRYPTION_TYPE" == "AWS_SSE_KMS" ]; then
                echo "      ENCRYPTION = ( TYPE = 'AWS_SSE_KMS' KMS_KEY_ID = '${S3_KMS_KEY_ID}' )"
            else
                echo "      ENCRYPTION = ( TYPE = '${S3_ENCRYPTION_TYPE}' )"
            fi
            cat << EOF
    )
  )
  ALLOW_WRITES = TRUE;

-- After running this, execute the following to get the AWS IAM user ARN:
-- DESC EXTERNAL VOLUME FLEET_ICEBERG_VOL;
-- 
-- Then update your S3 bucket policy and IAM role trust relationship with this ARN.
EOF
            ;;
        "GCS")
            cat << EOF
-- Create External Volume for Google Cloud Storage
CREATE OR REPLACE EXTERNAL VOLUME FLEET_ICEBERG_VOL
  STORAGE_LOCATIONS = (
    (
      NAME = 'fleet_gcs_storage'
      STORAGE_PROVIDER = 'GCS'
      STORAGE_BASE_URL = 'gcs://${GCS_BUCKET_NAME}/${GCS_PATH}'
    )
  )
  ALLOW_WRITES = TRUE;

-- After running this, execute the following to get the service account:
-- DESC EXTERNAL VOLUME FLEET_ICEBERG_VOL;
--
-- Then grant 'storage.objectAdmin' role on your bucket to this service account.
EOF
            ;;
        "AZURE")
            # Determine the storage URL based on OneLake vs standard Azure
            if [ "$USE_ONELAKE" == "true" ]; then
                AZURE_URL="azure://onelake.dfs.fabric.microsoft.com/${ONELAKE_WORKSPACE_GUID}/${ONELAKE_LAKEHOUSE_GUID}.Lakehouse/Files/${AZURE_PATH}"
                STORAGE_NAME="fleet_onelake_storage"
            else
                # Use dfs endpoint for ADLS Gen2 compatibility
                AZURE_URL="azure://${AZURE_STORAGE_ACCOUNT}.blob.core.windows.net/${AZURE_CONTAINER}/${AZURE_PATH}"
                STORAGE_NAME="fleet_azure_storage"
            fi
            cat << EOF
-- Create External Volume for Azure Storage
-- See: https://docs.snowflake.com/en/user-guide/tables-iceberg-configure-external-volume-azure
CREATE OR REPLACE EXTERNAL VOLUME FLEET_ICEBERG_VOL
  STORAGE_LOCATIONS = (
    (
      NAME = '${STORAGE_NAME}'
      STORAGE_PROVIDER = 'AZURE'
      STORAGE_BASE_URL = '${AZURE_URL}'
      AZURE_TENANT_ID = '${AZURE_TENANT_ID}'
    )
  )
  ALLOW_WRITES = TRUE;

-- After running this, execute the following to get consent URL:
-- DESC EXTERNAL VOLUME FLEET_ICEBERG_VOL;
--
-- Visit the AZURE_CONSENT_URL and grant permissions to the Snowflake application.
EOF
            ;;
        *)
            echo -e "${RED}Unknown storage provider: $STORAGE_PROVIDER${NC}"
            exit 1
            ;;
    esac
}

# Generate the SQL files
mkdir -p generated_sql

# Generate external volume SQL
generate_external_volume_sql > generated_sql/01_external_volume.sql
echo -e "${GREEN}Generated: generated_sql/01_external_volume.sql${NC}"

# Copy base SQL scripts (now in flat structure)
cp 02_create_database.sql generated_sql/
cp 03_create_iceberg_tables.sql generated_sql/
cp 04_create_dynamic_tables.sql generated_sql/
cp 05_create_governance.sql generated_sql/
cp 06_load_sample_data.sql generated_sql/
cp 07_create_agent.sql generated_sql/

# Update external volume references in SQL files based on configuration
if [ "$USE_EXISTING_VOLUME" == "true" ] && [ -n "$EXISTING_VOLUME_NAME" ]; then
    # Replace volume name in table definitions with existing volume
    sed -i.bak "s/FLEET_ICEBERG_VOL/$EXISTING_VOLUME_NAME/g" generated_sql/*.sql
    # Append ALTER DATABASE to the end of database creation script (after database exists)
    echo "" >> generated_sql/02_create_database.sql
    echo "-- Set default external volume for the database" >> generated_sql/02_create_database.sql
    echo "ALTER DATABASE $SNOWFLAKE_DATABASE SET EXTERNAL_VOLUME = '$EXISTING_VOLUME_NAME';" >> generated_sql/02_create_database.sql
else
    # Creating a new external volume - add ALTER DATABASE to set it as default
    echo "" >> generated_sql/02_create_database.sql
    echo "-- Set default external volume for the database" >> generated_sql/02_create_database.sql
    echo "ALTER DATABASE $SNOWFLAKE_DATABASE SET EXTERNAL_VOLUME = 'FLEET_ICEBERG_VOL';" >> generated_sql/02_create_database.sql
fi

echo ""
echo -e "${YELLOW}Step 3: Connecting to Snowflake and running setup...${NC}"
echo ""

# Run SQL files using Snowflake CLI
echo "Running SQL setup scripts..."

# Get absolute path to current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for sql_file in generated_sql/*.sql; do
    # Skip files that only contain comments
    if grep -q "^[^-]" "$sql_file" 2>/dev/null; then
        # Skip governance script on Standard edition
        if [[ "$sql_file" == *"05_create_governance"* ]] && [ "$GOVERNANCE_AVAILABLE" != "true" ]; then
            echo -e "  ${YELLOW}Skipping: $sql_file (requires Enterprise edition)${NC}"
            continue
        fi
        
        echo "  Running: $sql_file"
        abs_path="${SCRIPT_DIR}/${sql_file}"
        snow sql --connection="$SNOWFLAKE_CONNECTION" --filename="$abs_path"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error running $sql_file${NC}"
            echo "You may need to run this file manually in Snowsight."
        fi
    else
        echo "  Skipping: $sql_file (no executable SQL)"
    fi
done

# Upload sample JSON files (now in flat structure)
echo ""
echo "Uploading sample JSON files to stage..."
snow sql --connection="$SNOWFLAKE_CONNECTION" --query="PUT file://*.json @${SNOWFLAKE_DATABASE}.RAW.LOGS_STAGE AUTO_COMPRESS=FALSE"

# Upload semantic model for Cortex Agent
echo ""
echo "Uploading semantic model for Cortex Agent..."
snow sql --connection="$SNOWFLAKE_CONNECTION" --query="PUT file://fleet_semantic_model.yaml @${SNOWFLAKE_DATABASE}.RAW.LOGS_STAGE AUTO_COMPRESS=FALSE"

echo -e "${GREEN}SQL setup complete!${NC}"

# Network Policy for streaming (optional)
echo ""
if [ "$ENABLE_NETWORK_POLICY" == "true" ]; then
    echo -e "${YELLOW}Step 3b: Setting up network policy for streaming...${NC}"
    echo "Creating network policy to allow streaming connections..."
    
    # Get user's current IP and create a more specific rule
    echo "This will create a network policy allowing connections from any IP."
    echo "For production, edit 08_network_policy.sql to restrict to your IP."
    
    snow sql --connection="$SNOWFLAKE_CONNECTION" --filename="${SCRIPT_DIR}/08_network_policy.sql"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Network policy created!${NC}"
        echo -e "${YELLOW}NOTE: The policy is created but NOT applied by default.${NC}"
        echo "If you have connection issues with the streaming script, run:"
        echo "  ALTER USER <your_username> SET NETWORK_POLICY = FLEET_STREAMING_POLICY;"
    fi
else
    echo -e "${BLUE}Skipping network policy setup (ENABLE_NETWORK_POLICY not set to true)${NC}"
    echo "If you have connection issues with the streaming script from a VPN, set ENABLE_NETWORK_POLICY=true"
fi

# Setup Conda environment for Spark (optional)
echo ""
echo -e "${YELLOW}Step 4: Setting up Spark environment (optional)...${NC}"
if command -v conda &> /dev/null; then
    echo "Found Conda - creating fleet-spark environment..."
    
    if ! conda env list | grep -q "fleet-spark"; then
        conda create -n fleet-spark python=3.10 -y
        # Use conda run to install packages in the new environment
        conda run -n fleet-spark pip install pyspark==4.0.0 jupyter jupyterlab python-dotenv
        conda run -n fleet-spark pip install "pyiceberg[all]"
        echo -e "${GREEN}Spark environment 'fleet-spark' created${NC}"
        echo ""
        echo "To use the Spark environment:"
        echo "  conda activate fleet-spark"
        echo "  jupyter notebook spark_iceberg_interop.ipynb"
    else
        echo "Environment 'fleet-spark' already exists"
        echo "To ensure all packages are installed, run:"
        echo "  conda run -n fleet-spark pip install pyspark==4.0.0 jupyter jupyterlab python-dotenv 'pyiceberg[all]'"
    fi
else
    echo "Conda not found. To use the Spark interoperability section:"
    echo "1. Install Conda from https://docs.conda.io/en/latest/miniconda.html"
    echo "2. Run: conda create -n fleet-spark python=3.10 -y"
    echo "3. Run: conda activate fleet-spark"
    echo "4. Run: pip install pyspark==4.0.0 jupyter jupyterlab python-dotenv 'pyiceberg[all]'"
fi

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Show edition-specific notes
if [ "$GOVERNANCE_AVAILABLE" != "true" ]; then
    echo -e "${YELLOW}Note: Running on Standard Edition${NC}"
    echo "The following features require Enterprise edition and were skipped:"
    echo "  - Masking policies (Section: Security & Governance)"
    echo "  - Data Metric Functions (Section: Data Quality)"
    echo "  - Tags and classification"
    echo ""
    echo "You can still follow along with the guide - just skip those sections."
    echo ""
fi

echo "Next steps:"
echo ""
echo "1. Import the Snowflake Notebook into Snowsight:"
echo "   - Go to Projects » Notebooks in Snowsight"
echo "   - Click the arrow next to '+ Notebook' and select 'Import .ipynb file'"
echo "   - Select: fleet_analytics_notebook.ipynb"
echo "   - Set location to FLEET_ANALYTICS_DB.RAW and warehouse to FLEET_ANALYTICS_WH"
echo ""
echo "2. Start the streaming simulation (in a separate terminal):"
echo "   source iceberg_v3_demo_venv/bin/activate"
echo "   python stream_telemetry.py"
echo ""
echo "3. (Optional) For Spark interoperability section:"
echo "   conda activate fleet-spark"
echo "   jupyter notebook spark_iceberg_interop.ipynb"
echo ""
echo "4. Follow along with the guide!"
echo ""
