## Build a Multi-Tenant AI Chat App with Snowflake Cortex REST API

This folder contains the complete source code for the developer guide.

### Quick Start

```bash
bash setup.sh        # creates venv, installs deps, generates RSA keys
cp .env.example .env # then edit with your Snowflake account identifier
```

### SQL Scripts (run in Snowsight as ACCOUNTADMIN)

| Script | Description |
|--------|-------------|
| `01_rbac_setup.sql` | Create tenant roles, service users, register RSA public keys |
| `02_enable_model_rbac.sql` | Enable strict Model RBAC and grant models to tenant roles |
| `03_bonus_table_agent_rbac.sql` | Optional: grant table + Cortex Agent access to tenant roles |

### Running

```bash
source venv/bin/activate

# Terminal 1: FastAPI gateway
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Streamlit chat UI
cd streamlit_app && streamlit run streamlit_app.py --server.port 8501
```
