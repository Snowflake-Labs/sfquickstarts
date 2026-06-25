{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "6e4cf379-4ef2-4458-9451-bb063244bcc0",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "# ================================================================\n# SCENARIO 1 \u2014 DATABRICKS READS & WRITES SNOWFLAKE-MANAGED ICEBERG\n#\n# What this demonstrates:\n#   Demo 1 \u2014 Read OPEN_TABLE        \u2705 success\n#   Demo 2 \u2014 Read PROTECTED_TABLE   \u2705 success (raw Parquet, governance NOT applied)\n#   Demo 3 \u2014 Write OPEN_TABLE       \u2705 success (write-capable S3 creds vended)\n#   Demo 4 \u2014 Write PROTECTED_TABLE  \u274c blocked (read-only S3 creds vended \u2192 403)\n#   Demo 5 \u2014 Delete from OPEN_TABLE \u2705 success\n#\n# Prerequisites:\n#   1. Run 01_sf_iceberg_catalog_setup.sql in Snowflake first.\n#   2. Copy the PAT token from Step 8 of that script.\n#   3. Attach this notebook to Cluster Config A (NO Unity Catalog).\n#      See DEMO_SCRIPT.md \u2192 Cluster Configuration A.\n#   4. Install Maven library on the cluster before attaching:\n#        org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.9.1\n#      (use iceberg-spark-runtime-3.4_2.12:1.9.1 for DBR 13.3 LTS)\n#\n# !! REPLACE all <PLACEHOLDER> values below before running.\n# ================================================================",
   "id": "cell-0"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "9203d4ce-4d51-46bc-877f-3dde89f5f10c",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Step 0 \u2014 Configure Horizon IRC Catalog\nSet your Snowflake account details and PAT token here.",
   "id": "cell-1"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782404082540,
     "inputWidgets": {},
     "nuid": "ada54db1-13a9-41b4-a390-648bee9d0434",
     "showTitle": false,
     "startTime": 1782404082397,
     "submitTime": 1782404082311,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "# !! REPLACE: Snowflake account in hyphenated org-account format\n#    e.g. 'myorg-myaccount'  (find in Snowsight \u2192 Admin \u2192 Accounts \u2192 Account URL)\nSNOWFLAKE_ACCOUNT = \"<YOUR_ACCOUNT>\"          # org-account format, e.g. 'myorg-myaccount'   # org-account, lowercased\n\n# !! REPLACE: Snowflake role for Databricks (created by 01_sf_iceberg_catalog_setup.sql)\nSNOWFLAKE_ROLE    = \"EXT_COMPUTE_ENG_DEMO_ROLE\"\n\n# !! REPLACE: PAT token from ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN output\n#    Generate with Step 8 of 01_sf_iceberg_catalog_setup.sql.\n#    \u26a0  Never commit this value to source control.\nSNOWFLAKE_PAT     = \"<YOUR_PAT_TOKEN>\"\n\n# !! REPLACE: Snowflake database that is the Iceberg catalog\nSF_DATABASE       = \"HORIZON_DEMO_SFDB\"\n\nCATALOG_NAME = \"sf_horizon\"   # local Spark catalog alias \u2014 can be any name\n\nIRC_BASE_URL = f\"https://{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/polaris/api/catalog\"\nOAUTH_URL    = f\"{IRC_BASE_URL}/v1/oauth/tokens\"\n\n# \u2500\u2500 Register the Iceberg REST catalog with Spark \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}\",\n               \"org.apache.iceberg.spark.SparkCatalog\")\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.catalog-impl\",\n               \"org.apache.iceberg.rest.RESTCatalog\")\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.uri\",               IRC_BASE_URL)\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.oauth2-server-uri\", OAUTH_URL)\n\n# Horizon IRC: PAT as client_secret, no client_id \u2192 prepend ':' for empty client_id\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.credential\",  f\":{SNOWFLAKE_PAT}\")\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.scope\",       f\"session:role:{SNOWFLAKE_ROLE}\")\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.warehouse\",   SF_DATABASE)\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.io-impl\",                           \"org.apache.iceberg.aws.s3.S3FileIO\")\nspark.conf.set(f\"spark.sql.catalog.{CATALOG_NAME}.header.X-Iceberg-Access-Delegation\", \"vended-credentials\")\nspark.conf.set(f\"spark.sql.iceberg.vectorization.enabled\",    \"false\")\n\n\nprint(f\"Catalog  : {CATALOG_NAME}\")\nprint(f\"IRC URL  : {IRC_BASE_URL}\")\nprint(f\"Warehouse: {SF_DATABASE}\")\nprint(f\"Role     : {SNOWFLAKE_ROLE}\")\n",
   "id": "cell-2"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "73aca4d6-12ba-4f0f-8b18-b7184c1dfb2a",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Step 1 \u2014 Discover Catalog (verify connectivity)",
   "id": "cell-3"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782404087943,
     "inputWidgets": {},
     "nuid": "a6ffc492-d351-4044-922f-e2c8989f28d5",
     "showTitle": false,
     "startTime": 1782404086865,
     "submitTime": 1782404086831,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "# !! REPLACE: schema name (SF_DEMO_SCHEMA from 01_sf_iceberg_catalog_setup.sql)\nSF_SCHEMA = \"DEMO_SCHEMA\"\n\nprint(\"=== Namespaces (Schemas) ===\")\nspark.sql(f\"SHOW NAMESPACES IN {CATALOG_NAME}\").show()\n\nprint(f\"=== Tables in {SF_SCHEMA} ===\")\nspark.sql(f\"SHOW TABLES IN {CATALOG_NAME}.{SF_SCHEMA}\").show()\n",
   "id": "cell-4"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782404094154,
     "inputWidgets": {},
     "nuid": "2f7ca8c6-443f-4064-b6b1-6dacca389f04",
     "showTitle": false,
     "startTime": 1782404091547,
     "submitTime": 1782404091518,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "\n# Clear any stale cached metadata/credentials from the session\nspark.catalog.clearCache()\nspark.sql(f\"REFRESH TABLE {CATALOG_NAME}.DEMO_SCHEMA.OPEN_TABLE\")\n\nprint(\"=== READ: OPEN_TABLE ===\")\ndf_open = spark.table(f\"{CATALOG_NAME}.DEMO_SCHEMA.OPEN_TABLE\")\ndf_open.show(truncate=False)\nprint(f\"Row count: {df_open.count()}\")",
   "id": "cell-5"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "7b123772-7f5e-403f-9f30-ac93369e8858",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Demo 2 \u2014 Read: PROTECTED_TABLE  \u2705 expected: SUCCESS\n\nPROTECTED_TABLE carries Snowflake Horizon governance policies\n(column masking on sensitive_data, row access policy on created_at).\n\n\u26a0  IMPORTANT CAVEAT: Horizon IRC vends S3 credentials directly to Databricks.\nDatabricks reads raw Parquet \u2014 Snowflake SQL-engine policies are NOT applied.\nAll 3 rows are visible, sensitive_data is unmasked.\n\nGovernance policies DO apply when the table is queried via Snowflake SQL\n(demonstrated in 04_sf_federate_databricks_uc.sql governance section).",
   "id": "cell-6"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782371705618,
     "inputWidgets": {},
     "nuid": "4eee4dde-d7fd-47b2-b58c-64755c7c74c8",
     "showTitle": false,
     "startTime": 1782371703551,
     "submitTime": 1782371703514,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "print(\"=== READ: PROTECTED_TABLE (via Horizon IRC \u2014 raw Parquet path) ===\")\ndf_prot = spark.table(f\"{CATALOG_NAME}.{SF_SCHEMA}.PROTECTED_TABLE\")\ndf_prot.show(truncate=False)\nprint(f\"Row count: {df_prot.count()}\")\nprint()\nprint(\"Note: All 3 rows visible; sensitive_data is unmasked in Iceberg/S3 path.\")\nprint(\"Governance is enforced ONLY via Snowflake SQL, not IRC vended-credential reads.\")\n",
   "id": "cell-7"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782404153614,
     "inputWidgets": {},
     "nuid": "329cd1be-0bc6-4e75-8c35-ce93ebd950e1",
     "showTitle": false,
     "startTime": 1782404148180,
     "submitTime": 1782404148076,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "import requests# Step 1: Exchange PAT \u2192 OAuth access token\n\noauth_token = requests.post(\n    OAUTH_URL,\n    data={\n        \"grant_type\":    \"client_credentials\",\n        \"scope\":         f\"session:role:{SNOWFLAKE_ROLE}\",\n        \"client_secret\": SNOWFLAKE_PAT\n    }\n).json()[\"access_token\"]\n\n# Step 2: Read through Snowflake SQL engine with the OAuth token\ndf_governed = spark.read \\\n    .format(\"net.snowflake.spark.snowflake\") \\\n    .option(\"sfURL\",           f\"{SNOWFLAKE_ACCOUNT}.snowflakecomputing.com\") \\\n    .option(\"sfUser\",          \"<YOUR_USERNAME>\") \\\n    .option(\"sfAuthenticator\", \"oauth\") \\\n    .option(\"sfToken\",         oauth_token) \\\n    .option(\"sfRole\",          SNOWFLAKE_ROLE) \\\n    .option(\"sfWarehouse\",     \"LOAD_WH\") \\\n    .option(\"sfDatabase\",      \"HORIZON_DEMO_SFDB\") \\\n    .option(\"sfSchema\",        \"DEMO_SCHEMA\") \\\n    .option(\"dbtable\",         \"PROTECTED_TABLE\") \\\n    .load()\n\ndf_governed.show(truncate=False)",
   "id": "cell-8"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "fb5210a9-71e8-4770-9f05-2a2ca5bf9ee1",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Demo 3 \u2014 Write: OPEN_TABLE  \u2705 expected: SUCCESS\n\nEXT_COMPUTE_ENG_DEMO_ROLE has INSERT/UPDATE/DELETE on OPEN_TABLE.\nSnowflake vends write-capable S3 credentials \u2192 s3:PutObject succeeds.",
   "id": "cell-9"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782404176435,
     "inputWidgets": {},
     "nuid": "e1f65fd1-6c00-4b52-8518-c014e92a33a6",
     "showTitle": false,
     "startTime": 1782404170440,
     "submitTime": 1782404170408,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "print(\"=== WRITE: OPEN_TABLE ===\")\ntry:\n    spark.sql(f\"\"\"\n        INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE\n        VALUES (99, 'Demo Widget', 3, 19.99, current_timestamp())\n    \"\"\")\n    print(\"Write to OPEN_TABLE: SUCCESS\")\nexcept Exception as e:\n    print(\"Write BLOCKED \u2705 \u2014 WRONG.\")\n    print(f\"Exception : {type(e).__name__}\")\n    print(f\"Message   : {str(e)[:600]}\")\nprint()\nprint(\"=== OPEN_TABLE after insert ===\")\nspark.table(f\"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE\").orderBy(\"id\").show(truncate=False)\n",
   "id": "cell-10"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "034468a4-2ae9-4f73-9a99-b0bf05651e05",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Demo 4 \u2014 Write: PROTECTED_TABLE  \u274c expected: FAIL\n\nEXT_COMPUTE_ENG_DEMO_ROLE has SELECT only on PROTECTED_TABLE\n(no INSERT/UPDATE/DELETE \u2014 see PROTECTED_TABLE_RO database role).\nSnowflake vends READ-ONLY S3 credentials for this table.\nDatabricks tries to commit the Iceberg snapshot (s3:PutObject) \u2192 S3 returns 403.\n\nExpected error:\n  AmazonS3Exception: Access Denied (Status Code: 403; Error Code: AccessDenied)",
   "id": "cell-11"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782369120236,
     "inputWidgets": {},
     "nuid": "bc3f0019-b0fd-4cb5-99d1-d0652d173a47",
     "showTitle": false,
     "startTime": 1782369119223,
     "submitTime": 1782369119183,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "print(\"=== WRITE: PROTECTED_TABLE (expected to FAIL) ===\")\ntry:\n    spark.sql(f\"\"\"\n        INSERT INTO {CATALOG_NAME}.{SF_SCHEMA}.PROTECTED_TABLE\n        VALUES (99, 'Test User', 'TEST-DATA', 0.00, current_timestamp())\n    \"\"\")\n    print(\"ERROR: Write succeeded \u2014 verify PROTECTED_TABLE_RO has no write grants.\")\nexcept Exception as e:\n    print(\"Write BLOCKED \u2705 \u2014 as expected.\")\n    print(f\"Exception : {type(e).__name__}\")\n    print(f\"Message   : {str(e)[:600]}\")\n",
   "id": "cell-12"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "e44d0e8e-9331-4e08-a085-328b2c951d8b",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Demo 5 \u2014 Cleanup: Delete row from OPEN_TABLE  \u2705 expected: SUCCESS",
   "id": "cell-13"
  },
  {
   "cell_type": "code",
   "execution_count": 0,
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {
      "byteLimit": 2048000,
      "rowLimit": 10000
     },
     "finishTime": 1782403644435,
     "inputWidgets": {},
     "nuid": "397886ba-0988-461f-8428-af19de51a382",
     "showTitle": false,
     "startTime": 1782403638888,
     "submitTime": 1782403638801,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "outputs": [],
   "source": "print(\"=== DELETE from OPEN_TABLE (row id=99) ===\")\nspark.sql(f\"DELETE FROM {CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE WHERE id = 99\")\nprint(\"Delete: SUCCESS\")\n\nprint()\nprint(\"=== OPEN_TABLE after delete (back to 3 original rows) ===\")\nspark.table(f\"{CATALOG_NAME}.{SF_SCHEMA}.OPEN_TABLE\").orderBy(\"id\").show(truncate=False)\n",
   "id": "cell-14"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "680d1c22-4714-4020-a39c-743b20c16d0d",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Governance Comparison Summary\n\nRun these in a Snowflake worksheet to confirm policies apply via Snowflake SQL:\n\n```sql\n-- ACCOUNTADMIN: 3 rows, unmasked\nUSE ROLE ACCOUNTADMIN;\nSELECT * FROM <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE;\n\n-- DATABRICKS_DEMO_ROLE: 2 rows (2023 row filtered), *** MASKED ***\nUSE ROLE <SF_DATABRICKS_ROLE>;\nSELECT * FROM <SF_MANAGED_ICEBERG_DB>.<SF_DEMO_SCHEMA>.PROTECTED_TABLE;\n```\n\n| Access path                            | Rows | sensitive_data  |\n|----------------------------------------|------|-----------------|\n| Snowflake SQL (ACCOUNTADMIN)           |  3   | unmasked        |\n| Snowflake SQL (<SF_DATABRICKS_ROLE>)   |  2   | *** MASKED ***  |\n| Databricks via Horizon IRC (any role)  |  3   | unmasked        |\n\n\u2192 Snowflake Horizon governs the SQL path; credential vending governs writes.",
   "id": "cell-15"
  },
  {
   "cell_type": "markdown",
   "metadata": {
    "application/vnd.databricks.v1+cell": {
     "cellMetadata": {},
     "inputWidgets": {},
     "nuid": "bce35e50-2942-4ea5-b127-98c81611b8da",
     "showTitle": false,
     "tableResultSettingsMap": {},
     "title": ""
    }
   },
   "source": "## Horizon IRC Diagnostic (curl \u2014 run from terminal if connectivity fails)\n\n```bash\nACCOUNT=\"<SF_ACCOUNT_IDENTIFIER>\"\nDB=\"<SF_MANAGED_ICEBERG_DB>\"\nROLE=\"<SF_DATABRICKS_ROLE>\"\nPAT=\"<SF_PAT_TOKEN>\"\nBASE=\"https://${ACCOUNT}.snowflakecomputing.com/polaris/api/catalog\"\n\n# 1. Reachability\ncurl -i --max-time 15 \"${BASE}/v1/config?warehouse=${DB}\"\n\n# 2. Exchange PAT for bearer token\nTOKEN=$(curl -s -X POST \"${BASE}/v1/oauth/tokens\" \\\n  -H \"Content-Type: application/x-www-form-urlencoded\" \\\n  --data-urlencode \"grant_type=client_credentials\" \\\n  --data-urlencode \"scope=session:role:${ROLE}\" \\\n  --data-urlencode \"client_secret=${PAT}\" \\\n  | python3 -c \"import sys,json; print(json.load(sys.stdin)['access_token'])\")\n\n# 3. List namespaces\ncurl -i \"${BASE}/v1/${DB}/namespaces\" -H \"Authorization: Bearer $TOKEN\"\n\n# 4. Load table metadata\ncurl -i \"${BASE}/v1/${DB}/namespaces/<SF_DEMO_SCHEMA>/tables/OPEN_TABLE\" \\\n  -H \"Authorization: Bearer $TOKEN\" \\\n  -H \"X-Iceberg-Access-Delegation: vended-credentials\"\n```",
   "id": "cell-16"
  }
 ],
 "metadata": {
  "application/vnd.databricks.v1+notebook": {
   "computePreferences": null,
   "dashboards": [],
   "environmentMetadata": null,
   "inputWidgetPreferences": null,
   "language": "python",
   "notebookMetadata": {
    "pythonIndentUnit": 4
   },
   "notebookName": "03_databricks_rw_sf_iceberg 2026-06-25 06:05:19",
   "widgets": {}
  },
  "language_info": {
   "name": "python"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}