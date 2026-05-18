#!/bin/bash
# ============================================================
# Quick Setup Script
# ============================================================
# Creates the project, installs dependencies, and generates
# RSA key pairs for both tenants.
#
# Usage: bash setup.sh
# ============================================================

set -e

echo "=== Creating virtual environment ==="
python3 -m venv venv
source venv/bin/activate

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Generating RSA key pairs ==="
mkdir -p keys

# Alpha tenant
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out keys/alpha_rsa_key.p8 -nocrypt
openssl rsa -in keys/alpha_rsa_key.p8 -pubout -out keys/alpha_rsa_key.pub

# Beta tenant
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out keys/beta_rsa_key.p8 -nocrypt
openssl rsa -in keys/beta_rsa_key.p8 -pubout -out keys/beta_rsa_key.pub

echo "=== Setting up .env ==="
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example — edit it with your Snowflake account identifier."
else
    echo ".env already exists, skipping."
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env with your SNOWFLAKE_ACCOUNT identifier"
echo "  2. Run assets/01_rbac_setup.sql in Snowsight (replace RSA_PUBLIC_KEY values)"
echo "  3. Run assets/02_enable_model_rbac.sql in Snowsight"
echo "  4. Start the gateway:  source venv/bin/activate && python3 -m uvicorn app.main:app --port 8000 --reload"
echo "  5. Start Streamlit:    cd streamlit_app && streamlit run streamlit_app.py --server.port 8501"
