author: Brian Pace
id: snowflake-postgres-spcs-pgadmin-connect-via-privatelink
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Deploy pgAdmin to SPCS Connecting to Snowflake Postgres via Private Link
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Deploy pgAdmin to SPCS Connecting to Snowflake Postgres via Private Link
<!-- ------------------------ -->
## Overview 

### What You Will Build

This quickstart walks through deploying pgAdmin4 as a Snowpark Container Services (SPCS) service and connecting it to a Snowflake Postgres instance over Private Link. All database traffic stays on Snowflake's private network backbone and never leaves the Snowflake environment. This example uses the pgAdmin container as an example, but the same steps can be used to deploy other containers that need Postgres.

[pgAdmin](https://www.pgadmin.org/) is an open-source administration and development platform for PostgreSQL. It provides a web-based interface for managing databases, writing and executing queries, monitoring server activity, and visualizing data. Running pgAdmin inside SPCS rather than on an external machine eliminates the need to expose your Postgres instance to the public internet or configure VPN tunnels. The connection uses Private Link over Snowflake's internal network, reducing latency, simplifying network security, and ensuring that credentials and query traffic never traverse external networks.

> **Instance name placeholder:** All examples use `PG_LAB` as the Snowflake Postgres instance name. Substitute your own instance name throughout.

**Note:** Private Link requires Snowflake Business Critical edition or higher.

### Architecture

```
Browser
  |  HTTPS
  v
pgAdmin4 Service  (SPCS)
  |  TCP 5432 via EAI (PRIVATE_HOST_PORT rule)
  v
SPCS Private Link Endpoint  <- provisioned by SYSTEM$PROVISION_PRIVATELINK_ENDPOINT
  |  Snowflake private network
  v
Snowflake Postgres Instance  (Private Link Service)
```

### Key Components

| Component | Purpose |
|---|---|
| SPCS Compute Pool | Provides the compute resources that run the pgAdmin container |
| Image Repository | Stores the pgAdmin container image inside Snowflake |
| Snowflake Postgres Private Link | Exposes the Postgres instance as a Private Link Service on the Snowflake network |
| `SYSTEM$PROVISION_PRIVATELINK_ENDPOINT` | Creates the SPCS-side Private Link endpoint automatically without cloud portal work |
| External Access Integration (EAI) | Grants the container permission to open TCP connections to the private Postgres hostname |
| Snowflake Secret | Stores pgAdmin admin credentials; injected securely into the container as environment variables |

### Prerequisites

- Snowflake account with ACCOUNTADMIN access
- Snowflake CLI (`snow`) installed and configured
- Docker installed locally (for pulling and pushing the pgAdmin image)
- **Account-level Private Link already enabled** between your Snowflake account and your cloud network. See [AWS PrivateLink and Snowflake](https://docs.snowflake.com/en/user-guide/admin-security-privatelink) or [Azure Private Link and Snowflake](https://docs.snowflake.com/en/user-guide/privatelink-azure) for account-level setup if not already done.
- An active Snowflake Postgres instance (`PG_LAB` in these examples)

<!-- ------------------------ -->
## SPCS Infrastructure Setup

All SPCS objects (stage, image repository, service) live in a single database and schema to keep them organized.

### Step 1: Create Database, Schema, and Image Repository

```sql
-- SPCS Infrastructure Setup: Step 1 - Create Database, Schema, and Image Repository
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

CREATE DATABASE IF NOT EXISTS SPGAPP;
CREATE SCHEMA  IF NOT EXISTS SPGAPP.SPCS;

CREATE STAGE IF NOT EXISTS SPGAPP.SPCS.SPGAPP_STAGE;

CREATE IMAGE REPOSITORY IF NOT EXISTS SPGAPP.SPCS.IMAGES;
```

The stage holds service spec files and persistent data volumes. The image repository is the private Docker registry where you will push the pgAdmin image.

### Step 2: Create Compute Pool

The compute pool defines the virtual machine type that runs the container. A small CPU node (`CPU_X64_S`) is sufficient for pgAdmin.

```sql
-- SPCS Infrastructure Setup: Step 2 - Create Compute Pool
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

CREATE COMPUTE POOL IF NOT EXISTS SPGAPP_POOL
  MIN_NODES         = 1
  MAX_NODES         = 2
  INSTANCE_FAMILY   = 'CPU_X64_S'
  AUTO_RESUME       = TRUE
  AUTO_SUSPEND_SECS = 300;
```

`AUTO_SUSPEND_SECS = 300` suspends the pool after 5 minutes of inactivity to avoid idle credit consumption.

### Step 3: Push the pgAdmin Image to the Snowflake Registry

SPCS requires images to be stored in its own registry. The steps below pull the official pgAdmin image, re-tag it for your Snowflake registry, and push it.

```bash
# 1. Get your registry URL (returns something like abc123.registry.snowflakecomputing.com)
snow spcs image-registry url -c <your-connection>

# 2. Authenticate Docker to the Snowflake registry
snow spcs image-registry login -c <your-connection>

# 3. Pull the source image for the required architecture
#    SPCS runs on linux/amd64 - always specify the platform when pulling on Apple Silicon
docker pull --platform linux/amd64 dpage/pgadmin4:latest

# 4. Tag it for the Snowflake registry (image paths must be lowercase)
docker tag dpage/pgadmin4:latest <registry-url>/spgapp/spcs/images/pgadmin4:latest

# 5. Push to the Snowflake registry
docker push <registry-url>/spgapp/spcs/images/pgadmin4:latest
```

<!-- ------------------------ -->
## Enable Private Link on Postgres Instance

Private Link for a Snowflake Postgres instance is enabled per instance, independently of the account-level Private Link. The operation is asynchronous and can take up to 10 minutes.

### Step 1: Enable Private Link

```sql
-- Enable Private Link on Postgres Instance: Step 1 - Enable Private Link
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

ALTER POSTGRES INSTANCE PG_LAB ENABLE PRIVATELINK;
```

### Step 2: Wait for Private Link to Become Available

Poll `DESCRIBE POSTGRES INSTANCE` until `privatelink_service_identifier` is populated.

```sql
-- Enable Private Link on Postgres Instance: Step 2 - Wait for Private Link to Become Available
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

DESCRIBE POSTGRES INSTANCE PG_LAB;
```

### Step 3: Capture Connection Details

Once `privatelink_service_identifier` is populated, store the values for use in subsequent steps:

```sql
-- Enable Private Link on Postgres Instance: Step 3 - Capture Connection Details
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

SET plinksi     = '<privatelink_service_identifier value from DESCRIBE>';
SET pghost      = '<host value from DESCRIBE>';
SET pghost_port = $pghost || ':5432';
```

`$pghost_port` combines the hostname with the PostgreSQL port. It is used when defining the egress network rule later, which requires `host:port` format.

<!-- ------------------------ -->
## Provision the SPCS Private Link Endpoint

`SYSTEM$PROVISION_PRIVATELINK_ENDPOINT` is the key step that makes this approach different from a standard cloud Private Link setup. Instead of manually creating an Azure Private Endpoint or AWS VPC Endpoint in the cloud portal, this Snowflake function handles the cloud provider plumbing automatically within the SPCS network fabric. It creates a private endpoint that routes traffic from any SPCS container directly to the Postgres instance's Private Link Service over Snowflake's internal backbone.

### Step 1: Provision the Endpoint

```sql
-- Provision the SPCS Private Link Endpoint: Step 1 - Provision the Endpoint
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

SELECT SYSTEM$PROVISION_PRIVATELINK_ENDPOINT($plinksi, $pghost);
```

### Step 2: Authorize the Connection

After provisioning, a connection request appears on the Postgres instance in `PENDING` state. Retrieve its `connection_id` and authorize it:

```sql
-- Provision the SPCS Private Link Endpoint: Step 2 - Authorize the Connection
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

SHOW PRIVATELINK CONNECTIONS IN POSTGRES INSTANCE PG_LAB;

ALTER POSTGRES INSTANCE PG_LAB AUTHORIZE PRIVATELINK CONNECTIONS = ('<connection_id from SHOW PRIVATELINK CONNECTIONS>');
```

### Step 3: Verify the Connection

```sql
-- Provision the SPCS Private Link Endpoint: Step 3 - Verify the Connection
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

SHOW PRIVATELINK CONNECTIONS IN POSTGRES INSTANCE PG_LAB;
```

The status should now show `APPROVED`.

<!-- ------------------------ -->
## Configure SPCS Network Access

SPCS containers are network-isolated by default. To allow the pgAdmin container to open a TCP connection to the Postgres private endpoint, you must create an egress network rule, a secret for credentials, and an External Access Integration.

### Step 1: Create the Egress Network Rule

The `PRIVATE_HOST_PORT` type is specifically designed for Private Link targets. It instructs SPCS to route the connection through the provisioned Private Link endpoint rather than over the public internet.

```sql
-- Configure SPCS Network Access: Step 1 - Create the Egress Network Rule
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;
USE SCHEMA SPGAPP.SPCS;

CREATE OR REPLACE NETWORK RULE spg_private_rule
  MODE       = EGRESS
  TYPE       = PRIVATE_HOST_PORT
  VALUE_LIST = ($pghost_port);
```

### Step 2: Create the pgAdmin Credentials Secret

Snowflake Secrets store sensitive values and inject them into containers as environment variables at runtime. pgAdmin uses `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD` to create the initial admin account on first startup.

```sql
-- Configure SPCS Network Access: Step 2 - Create the pgAdmin Credentials Secret
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;
USE SCHEMA SPGAPP.SPCS;

CREATE OR REPLACE SECRET pgadmin_password
  TYPE     = PASSWORD
  USERNAME = 'admin@example.com'
  PASSWORD = 'change-me-before-production';
```

> **Security note:** Change the password to something strong before deploying. The secret value is encrypted at rest and only decrypted at container start time.

### Step 3: Create the External Access Integration

The External Access Integration (EAI) binds the network rule and the secret together into a single object that can be attached to a service. A service can only reach network targets and access secrets that are explicitly listed in its EAI.

```sql
-- Configure SPCS Network Access: Step 3 - Create the External Access Integration
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION spg_pg_lab_eai
  ALLOWED_NETWORK_RULES          = (spgapp.spcs.spg_private_rule)
  ALLOWED_AUTHENTICATION_SECRETS = (spgapp.spcs.pgadmin_password)
  ENABLED                        = TRUE;
```

<!-- ------------------------ -->
## Deploy the pgAdmin Service

### Step 1: Create the Service

The service spec defines the container image, environment variables, ports, health check, and volumes.

```sql
-- Deploy the pgAdmin Service: Step 1 - Create the Service
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;
USE SCHEMA SPGAPP.SPCS;

CREATE SERVICE IF NOT EXISTS PGADMIN4
  IN COMPUTE POOL SPGAPP_POOL
  MIN_INSTANCES = 1
  MAX_INSTANCES = 1
  FROM SPECIFICATION $$
spec:
  containers:
    - name: pgadmin4
      image: "/spgapp/spcs/images/pgadmin4:latest"
      secrets:
        - snowflakeSecret: spgapp.spcs.pgadmin_password
          secretKeyRef: username
          envVarName: PGADMIN_DEFAULT_EMAIL
        - snowflakeSecret: spgapp.spcs.pgadmin_password
          secretKeyRef: password
          envVarName: PGADMIN_DEFAULT_PASSWORD
      env:
        PGADMIN_LISTEN_ADDRESS:                    "0.0.0.0"
        PGADMIN_LISTEN_PORT:                       "80"
        PGADMIN_DISABLE_POSTFIX:                   "1"
        PGADMIN_CONFIG_ENHANCED_COOKIE_PROTECTION: "False"
      readinessProbe:
        port: 80
        path: /misc/ping
      volumeMounts:
        - name: pgadmin-data
          mountPath: /var/lib/pgadmin
  endpoints:
    - name: http
      port: 80
      public: true
  volumes:
    - name: pgadmin-data
      source: local
      uid: 5050
      gid: 5050
$$;
```

**Key spec settings:**

| Setting | Purpose |
|---|---|
| `secrets` | Injects credentials from the Snowflake Secret at container start |
| `PGADMIN_CONFIG_ENHANCED_COOKIE_PROTECTION: "False"` | Required when pgAdmin runs behind a reverse proxy (SPCS terminates TLS) |
| `PGADMIN_DISABLE_POSTFIX: "1"` | Disables the built-in mail server (not needed in SPCS) |
| `source: local` | Block storage for pgAdmin's internal SQLite database; stage-backed volumes cause SQLite locking errors |
| `uid: 5050 / gid: 5050` | pgAdmin runs as the `pgadmin` user; the volume must be writable by this UID |
| `readinessProbe` | SPCS waits for `/misc/ping` to return HTTP 200 before routing traffic to the container |

### Step 2: Attach the External Access Integration

The EAI must be attached after the service is created to allow the container to reach the Postgres private endpoint.

```sql
-- Deploy the pgAdmin Service: Step 2 - Attach the External Access Integration
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

ALTER SERVICE SPGAPP.SPCS.PGADMIN4
  SET EXTERNAL_ACCESS_INTEGRATIONS = (spg_pg_lab_eai);
```

### Step 3: Grant Access to the Service Endpoint

By default only ACCOUNTADMIN can use a new service. Grant your role access to the public HTTP endpoint:

```sql
-- Deploy the pgAdmin Service: Step 3 - Grant Access to the Service Endpoint
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

GRANT SERVICE ROLE SPGAPP.SPCS.PGADMIN4!ALL_ENDPOINTS_USAGE TO ROLE <your_role>;
```

### Step 4: Wait for the Service to Start

Service startup typically takes 1-3 minutes while the compute pool provisions and the container passes its readiness probe.

```sql
-- Deploy the pgAdmin Service: Step 4 - Wait for the Service to Start
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

DESCRIBE SERVICE SPGAPP.SPCS.PGADMIN4;

SHOW ENDPOINTS IN SERVICE SPGAPP.SPCS.PGADMIN4;
```

The `ingress_url` will be an address like:
`https://abc123-...-spgapp-spcs-pgadmin4.snowflakecomputing.app`

<!-- ------------------------ -->
## Connect pgAdmin to Snowflake Postgres

Open the `ingress_url` in your browser. The first login you will see is your Snowflake authentication to access the endpoint, not the pgAdmin authentication.

After authenticating with Snowflake, log in to pgAdmin with the credentials stored in the `pgadmin_password` secret (`admin@example.com` / `change-me-before-production` unless you changed them).

### Register the Snowflake Postgres Connection

In pgAdmin: **Object > Register > Server**, then fill in the tabs:

**General tab:**

| Field | Value |
|---|---|
| Name | `PG_LAB` (or any label you prefer) |

**Connection tab:**

| Field | Value |
|---|---|
| Host name/address | The `host` value from `DESCRIBE POSTGRES INSTANCE PG_LAB` |
| Port | `5432` |
| Maintenance database | `postgres` |
| Username | Your Snowflake Postgres admin user (e.g. `snowflake_admin`) |
| Password | Your Snowflake Postgres password |

**SSL tab:**

| Field | Value |
|---|---|
| SSL mode | `Require` |

> Snowflake Postgres requires TLS on all connections. Setting SSL mode to `Require` (or higher) is mandatory.

Click **Save**. pgAdmin will open a connection through the Private Link endpoint. All traffic travels over Snowflake's private network backbone with no exposure to the public internet.

<!-- ------------------------ -->
## Monitoring and Troubleshooting

### Check Service Status

```bash
snow spcs service describe SPGAPP.SPCS.PGADMIN4 -c <your-connection>
snow spcs service list-instances SPGAPP.SPCS.PGADMIN4 -c <your-connection>
```

### View Container Logs

```bash
snow spcs service logs SPGAPP.SPCS.PGADMIN4 \
  --container-name pgadmin4 \
  --instance-id 0 \
  -c <your-connection>
```

### Common Issues

| Symptom | Likely Cause | Fix |
|---|---|---|
| Service stuck in `PENDING` | Compute pool still starting | Wait 2-3 min; check `SHOW COMPUTE POOLS` |
| Service immediately `FAILED` | Bad spec or image path | Check logs; verify image path is lowercase and image was pushed |
| Endpoint returns 502/503 | Container not ready | Watch logs; confirm readiness probe at `/misc/ping` is passing |
| Can't connect to Postgres from pgAdmin | Missing or wrong EAI | Verify `ALTER SERVICE ... SET EXTERNAL_ACCESS_INTEGRATIONS` was run; check network rule `VALUE_LIST` includes the correct `host:5432` |
| Postgres connection timeout | Private Link endpoint not approved | Re-run `SHOW PRIVATELINK CONNECTIONS IN POSTGRES INSTANCE PG_LAB` and confirm status is `APPROVED` |
| pgAdmin login page doesn't load | Cookie protection mismatch | Confirm `PGADMIN_CONFIG_ENHANCED_COOKIE_PROTECTION: "False"` is set in the spec |
| `SYSTEM$PROVISION_PRIVATELINK_ENDPOINT` fails | Account-level Private Link not enabled | Complete account-level Private Link setup first (see Prerequisites) |

### Suspend and Resume to Save Credits

Suspending the service stops the compute pool from consuming credits when pgAdmin is not needed. Connection definitions survive a suspend/resume cycle because they are stored on the `local` volume (which persists while the pool is suspended, but **not** if the pool is dropped).

```sql
-- Suspend and resume the service
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

ALTER SERVICE      SPGAPP.SPCS.PGADMIN4 SUSPEND;
ALTER SERVICE      SPGAPP.SPCS.PGADMIN4 RESUME;

ALTER COMPUTE POOL SPGAPP_POOL SUSPEND;
ALTER COMPUTE POOL SPGAPP_POOL RESUME;
```

<!-- ------------------------ -->
## Cleanup

### Step 1: Revoke Private Link and Drop Service

```sql
-- Cleanup: Step 1 - Revoke Private Link and Drop Service
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

ALTER POSTGRES INSTANCE PG_LAB REVOKE PRIVATELINK CONNECTIONS = ($connid);

DROP SERVICE           IF EXISTS SPGAPP.SPCS.PGADMIN4;
DROP INTEGRATION       IF EXISTS spg_pg_lab_eai;
DROP NETWORK RULE      IF EXISTS spgapp.spcs.spg_private_rule;
DROP SECRET            IF EXISTS spgapp.spcs.pgadmin_password;
```

### Step 2: Drop Compute and Storage (Optional)

```sql
-- Cleanup: Step 2 - Drop Compute and Storage (Optional)
-- Execute in: Snowsight (Snowflake)
USE ROLE ACCOUNTADMIN;

ALTER COMPUTE POOL    SPGAPP_POOL SUSPEND;
DROP COMPUTE POOL     IF EXISTS SPGAPP_POOL;
DROP IMAGE REPOSITORY IF EXISTS SPGAPP.SPCS.IMAGES;
DROP STAGE            IF EXISTS SPGAPP.SPCS.SPGAPP_STAGE;
DROP SCHEMA           IF EXISTS SPGAPP.SPCS;
DROP DATABASE         IF EXISTS SPGAPP;
```

<!-- ------------------------ -->
## Conclusion and Resources

### What You Learned

Congratulations! You have successfully:

- Created the SPCS infrastructure (compute pool, image repository, stage)
- Pushed the pgAdmin container image to the Snowflake registry
- Enabled Private Link on a Snowflake Postgres instance
- Provisioned and authorized the SPCS Private Link endpoint
- Configured network access with egress rules and an External Access Integration
- Deployed pgAdmin4 as an SPCS service
- Connected pgAdmin to Snowflake Postgres over Private Link with no public internet exposure

### Key Capabilities Demonstrated

| SPCS | Snowflake Postgres |
|---|---|
| Container service deployment | Private Link Service |
| External Access Integration (EAI) | `SYSTEM$PROVISION_PRIVATELINK_ENDPOINT` |
| Private network egress rules | Connection authorization |
| Secrets for credential injection | TLS-required connections |

### Related Resources

- [Snowpark Container Services Documentation](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/overview)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/about)
- [AWS PrivateLink and Snowflake](https://docs.snowflake.com/en/user-guide/admin-security-privatelink)
- [Azure Private Link and Snowflake](https://docs.snowflake.com/en/user-guide/privatelink-azure)
