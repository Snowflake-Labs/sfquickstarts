author: Gilberto Hernandez, Oskar Lorek
id: configure-cicd-integrations-with-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/platform
language: en
summary: Configure CI/CD integrations for Snowflake using the Snowflake CLI GitHub Action, the Snowflake CI/CD Component for GitLab, and the Snowflake CLI Azure DevOps Extension with OIDC authentication.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Configure CI/CD Integrations with Snowflake

<!-- ------------------------ -->
## Overview

CI/CD pipelines let you automate Snowflake deployments so that changes are triggered by pull requests, merges, or scheduled runs rather than manual steps. Snowflake publishes first-party integrations for the most popular CI/CD platforms, each of which installs the Snowflake CLI on the runner and configures authentication to your Snowflake account.

In this Quickstart, we'll walk through configuring three of those integrations:

- **GitHub Actions** — using the [snowflakedb/snowflake-cli-action](https://github.com/snowflakedb/snowflake-cli-action) GitHub Action
- **GitLab CI/CD** — using the [Snowflake CI/CD Component](https://gitlab.com/snowflakedbutils/snowflake-cicd-component) from the GitLab CI/CD Catalog
- **Azure DevOps** — using the [ConfigureSnowflakeCLI@0](https://github.com/snowflakedb/snowflake-ado-extension) Azure Pipelines task

All three integrations support workload identity federation (WIF) with OpenID Connect (OIDC), which means your pipelines can authenticate to Snowflake with short-lived tokens instead of long-lived secrets. We'll focus on OIDC as the recommended approach and cover key-pair and password alternatives briefly.

This guide is structured so that you can follow one integration, two, or all three. Each platform section is self-contained.

### What You'll Learn

- How Snowflake CI/CD integrations work at a high level
- How to create a Snowflake service user with OIDC workload identity for GitHub Actions
- How to configure a GitHub Actions workflow that authenticates to Snowflake
- How to create a Snowflake service user with OIDC workload identity for GitLab CI/CD
- How to configure a GitLab CI/CD pipeline using the Snowflake CI/CD Component
- How to set up an Azure Entra ID App Registration with a federated credential for Azure DevOps
- How to configure an Azure Pipeline that authenticates to Snowflake
- How to troubleshoot common OIDC authentication issues

### What You'll Need

- A [Snowflake account](https://signup.snowflake.com/)
- A Snowflake user with **ACCOUNTADMIN** or **SECURITYADMIN** privileges
- For the GitHub Actions section: a GitHub repository with GitHub Actions enabled
- For the GitLab CI/CD section: a GitLab project (on GitLab.com or a self-managed instance with CI/CD enabled)
- For the Azure DevOps section: an Azure DevOps organization and project with Pipelines enabled, and an Azure subscription with permissions to create App Registrations in Microsoft Entra ID
- Snowflake CLI version 3.11 or later (for OIDC authentication)

### What You'll Build

- A GitHub Actions workflow that installs the Snowflake CLI, authenticates via OIDC, and runs Snowflake CLI commands
- A GitLab CI/CD pipeline that installs the Snowflake CLI via the Snowflake CI/CD Component, authenticates via OIDC, and runs Snowflake CLI commands
- An Azure DevOps pipeline that installs the Snowflake CLI, authenticates via OIDC through an Azure service connection, and runs Snowflake CLI commands

<!-- ------------------------ -->
## How Snowflake CI/CD Integrations Work

Before diving into platform-specific configuration, let's look at the concepts that are shared across all Snowflake CI/CD integrations.

### Service Users

Every CI/CD pipeline authenticates to Snowflake as a **service user** — a non-human user created specifically for automation. You create this user in Snowflake with `TYPE = SERVICE` and grant it only the roles the pipeline needs.

### Authentication with OIDC

Snowflake recommends workload identity federation (WIF) with OIDC for CI/CD. Here's how it works:

1. The CI runner requests a short-lived identity token from the platform's OIDC provider (GitHub, GitLab, Azure Entra ID).
2. The Snowflake CLI presents that token to Snowflake.
3. Snowflake validates the token's issuer and subject claims against the service user's `WORKLOAD_IDENTITY` configuration.
4. If the claims match, Snowflake creates a session. No passwords or private keys are involved.

Each platform has a different OIDC issuer URL and subject claim format. The platform-specific sections below provide the exact values.

### Snowflake CLI on the Runner

Each first-party integration installs the Snowflake CLI (`snow`) on the CI runner. After the setup step completes, `snow` is available on `PATH` for all subsequent steps. You can then run commands like `snow connection test`, `snow dcm deploy`, `snow sql`, or `snow app deploy`.

### Configuration Precedence

Most CI/CD workflows combine a committed **config.toml** file (containing connection metadata but no credentials) with secrets injected through environment variables. The precedence rules are:

1. Command-line parameters override everything.
2. Environment variables targeting a specific connection parameter (e.g. `SNOWFLAKE_CONNECTIONS_MYCONNECTION_ACCOUNT`) override **config.toml**.
3. Values defined in **config.toml** are used when no override is provided.
4. Generic environment variables such as `SNOWFLAKE_USER` apply last.

<!-- ------------------------ -->
## GitHub Actions: Set Up OIDC Authentication

In this section, we'll configure the Snowflake side of the integration by creating a service user that trusts GitHub's OIDC provider.

### Create a Snowflake Service User

Connect to Snowflake with a user that has **ACCOUNTADMIN** or **SECURITYADMIN** privileges and run the following:

```sql
CREATE USER github_cicd_user
  TYPE = SERVICE
  WORKLOAD_IDENTITY = (
    TYPE = OIDC
    ISSUER = 'https://token.actions.githubusercontent.com'
    SUBJECT = '<your_subject_claim>'
  );

GRANT ROLE <deployment_role> TO USER github_cicd_user;
```

Here's what the code does:

- Creates a service user named `github_cicd_user` that trusts GitHub's OIDC token issuer
- Configures the `SUBJECT` claim to restrict which repositories, branches, or environments can authenticate
- Grants a deployment role so the pipeline can manage Snowflake objects

### Determine Your Subject Claim

The subject claim controls which GitHub context is allowed to authenticate. Replace `<your_subject_claim>` with the value that matches your use case:

| Scope | Subject Claim |
| --- | --- |
| Specific repo + branch | `repo:my-org/my-repo:ref:refs/heads/main` |
| Specific repo (any branch) | `repo:my-org/my-repo:*` |
| Specific environment | `repo:my-org/my-repo:environment:production` |

For more details, see the [GitHub OIDC subject claim documentation](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect#example-subject-claims).

### Store Your Account Identifier as a GitHub Secret

1. Go to your GitHub repository **Settings > Secrets and variables > Actions**.
2. Click **New repository secret**.
3. Add a secret named `SNOWFLAKE_ACCOUNT` with your Snowflake account identifier as the value.

<!-- ------------------------ -->
## GitHub Actions: Configure the Workflow

Now let's create the GitHub Actions workflow that uses the Snowflake CLI GitHub Action to install the CLI and authenticate with OIDC.

### Create the Workflow File

Create or update your workflow file (e.g. **.github/workflows/deploy.yml**):

```yaml
name: Deploy to Snowflake
on:
  push:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false

      - name: Install and configure Snowflake CLI
        uses: snowflakedb/snowflake-cli-action@v2.0.2
        with:
          use-oidc: true
          cli-version: "3.16"

      - name: Verify connection and deploy
        env:
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: github_cicd_user
        run: |
          snow connection test -x
          snow dcm deploy --target PROD -x
```

Here's what the code does:

- Sets `id-token: write` permission, which is required for the runner to request a GitHub OIDC token
- Uses `snowflakedb/snowflake-cli-action@v2.0.2` to install the Snowflake CLI and configure OIDC authentication
- Runs `snow connection test -x` to verify the connection, then `snow dcm deploy` to deploy changes
- The `-x` flag indicates a temporary connection (no **config.toml** required)

> **Note:** Pin the action to an immutable tag like `@v2.0.2` for reproducible pipelines. A floating `@v2` tag will be available in the future to auto-update to the latest `v2.x` release.

### Verify the Pipeline

Push a commit to your `main` branch to trigger the workflow. In the GitHub Actions logs, you should see:

- The Snowflake CLI installed successfully
- `snow connection test -x` returning a successful connection result

### Alternative: Key-Pair Authentication

If OIDC is not available, you can use key-pair authentication. Store your private key as a GitHub secret and pass it through environment variables.

**Temporary connection (no config.toml):**

```yaml
- name: Install Snowflake CLI
  uses: snowflakedb/snowflake-cli-action@v2.0.2

- name: Deploy
  env:
    SNOWFLAKE_AUTHENTICATOR: SNOWFLAKE_JWT
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_PRIVATE_KEY_RAW: ${{ secrets.SNOWFLAKE_PRIVATE_KEY_RAW }}
    PRIVATE_KEY_PASSPHRASE: ${{ secrets.PASSPHRASE }}
  run: snow connection test -x
```

**Named connection (with config.toml):**

Commit a **config.toml** with an empty connection block:

```toml
default_connection_name = "myconnection"

[connections.myconnection]
```

Then override the connection fields through environment variables:

```yaml
- name: Install and configure Snowflake CLI
  uses: snowflakedb/snowflake-cli-action@v2.0.2
  with:
    default-config-file-path: "config.toml"

- name: Deploy
  env:
    SNOWFLAKE_CONNECTIONS_MYCONNECTION_AUTHENTICATOR: SNOWFLAKE_JWT
    SNOWFLAKE_CONNECTIONS_MYCONNECTION_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_CONNECTIONS_MYCONNECTION_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_CONNECTIONS_MYCONNECTION_PRIVATE_KEY_RAW: ${{ secrets.SNOWFLAKE_PRIVATE_KEY_RAW }}
  run: snow connection test
```

> **Note:** When using named connections, environment variables follow the format `SNOWFLAKE_CONNECTIONS_<CONNECTION_NAME>_<KEY>`. The connection name must match the name in **config.toml** (uppercased).

### Alternative: Password Authentication

Password authentication is supported but not recommended for production CI/CD. Store your password as a GitHub secret and pass it through environment variables:

```yaml
- name: Install Snowflake CLI
  uses: snowflakedb/snowflake-cli-action@v2.0.2

- name: Deploy
  env:
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
  run: snow connection test -x
```

<!-- ------------------------ -->
## GitLab CI/CD: Set Up OIDC Authentication

In this section, we'll configure the Snowflake side of the integration by creating a service user that trusts GitLab's OIDC provider.

### Create a Snowflake Service User

Connect to Snowflake with a user that has **ACCOUNTADMIN** or **SECURITYADMIN** privileges and run the following:

```sql
CREATE USER gitlab_cicd_user
  TYPE = SERVICE
  WORKLOAD_IDENTITY = (
    TYPE = OIDC
    ISSUER = 'https://gitlab.com'
    SUBJECT = '<your_subject_claim>'
  );

GRANT ROLE <deployment_role> TO USER gitlab_cicd_user;
```

Here's what the code does:

- Creates a service user named `gitlab_cicd_user` that trusts GitLab's OIDC token issuer
- Configures the `SUBJECT` claim to restrict which projects, branches, or tags can authenticate
- Grants a deployment role so the pipeline can manage Snowflake objects

### Determine Your Subject Claim

The subject claim controls which GitLab context is allowed to authenticate. Replace `<your_subject_claim>` with the value that matches your use case. GitLab OIDC tokens use the following subject format:

```
project_path:<group>/<project>:ref_type:<type>:ref:<ref_name>
```

| Scope | Subject Claim |
| --- | --- |
| Specific project + branch | `project_path:mygroup/myproject:ref_type:branch:ref:main` |
| Specific project + tag | `project_path:mygroup/myproject:ref_type:tag:ref:v1.0.0` |

For more details on customizing the subject, see the [GitLab OIDC documentation](https://docs.gitlab.com/ci/secrets/id_token_authentication/).

> **Note:** For self-managed GitLab instances, replace the issuer `https://gitlab.com` with the URL of your GitLab instance (e.g. `https://gitlab.example.com`).

### Store Your Credentials as GitLab CI/CD Variables

1. In your GitLab project, go to **Settings > CI/CD > Variables**.
2. Click **Add variable** and add:

| Key | Value | Flags |
| --- | --- | --- |
| `SNOWFLAKE_ACCOUNT` | Your [Snowflake account identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier) | Protected, Masked |
| `SNOWFLAKE_USER` | `gitlab_cicd_user` (the service user from the previous step) | Protected |

<!-- ------------------------ -->
## GitLab CI/CD: Configure the Pipeline

Now let's create the GitLab CI/CD pipeline that uses the Snowflake CI/CD Component to install the CLI and authenticate with OIDC.

### Create the Pipeline File

Create or update your **.gitlab-ci.yml** file:

```yaml
include:
  - component: $CI_SERVER_FQDN/snowflakedbutils/snowflake-cicd-component/configure-snowflake-cli@1.0.0
    inputs:
      use-oidc: true
      cli-version: "3.16"
      stage: build

stages: [build, deploy]

deploy:
  extends: .configure-snowflake-cli
  stage: deploy
  script:
    - snow connection test -x
    - snow dcm deploy --target PROD -x
  variables:
    SNOWFLAKE_ACCOUNT: $SNOWFLAKE_ACCOUNT
    SNOWFLAKE_USER: $SNOWFLAKE_USER
```

Here's what the code does:

- Uses `$CI_SERVER_FQDN` to automatically resolve the GitLab instance hostname (e.g. `gitlab.com`)
- The component's `configure-snowflake-cli` job runs in the `build` stage and installs the CLI
- The `use-oidc: true` input triggers GitLab to generate an ID token (`SNOWFLAKE_OIDC_TOKEN`) and configures the Snowflake authentication environment variables
- The `deploy` job extends `.configure-snowflake-cli` to inherit the CLI setup
- The `-x` flag indicates a temporary connection (no **config.toml** required)

### Verify the Pipeline

Push a commit to trigger the pipeline. In the GitLab CI/CD job logs, you should see:

- The `configure-snowflake-cli` job installs the CLI and configures OIDC
- The `deploy` job runs `snow connection test -x` returning a successful connection result

### Alternative: Key-Pair Authentication (Temporary Connection)

If OIDC is not available, you can use key-pair authentication. Store your private key as a CI/CD variable and pass it through environment variables.

First, add the following CI/CD variables in **Settings > CI/CD > Variables**:

| Key | Value | Flags |
| --- | --- | --- |
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier | Protected, Masked |
| `SNOWFLAKE_USER` | Your Snowflake username | Protected |
| `SNOWFLAKE_AUTHENTICATOR` | `SNOWFLAKE_JWT` | Protected |
| `SNOWFLAKE_PRIVATE_KEY_RAW` | Private key content (PEM format) | Protected, Masked |
| `PRIVATE_KEY_PASSPHRASE` | *(Optional)* Passphrase if the key is encrypted | Protected, Masked |

Then configure the pipeline:

```yaml
include:
  - component: $CI_SERVER_FQDN/snowflakedbutils/snowflake-cicd-component/configure-snowflake-cli@1.0.0
    inputs:
      stage: build

stages: [build, deploy]

deploy:
  stage: deploy
  script:
    - snow connection test -x
```

The CI/CD variables you set are automatically available as environment variables to all jobs. The Snowflake CLI reads them for authentication when using temporary connections (`-x` flag).

### Alternative: Key-Pair Authentication (Named Connection)

Use this method when you want to define named connections in a **config.toml** file and override credentials via CI/CD variables.

Commit a **config.toml** to your repository (no credentials):

```toml
default_connection_name = "default"

[connections.default]
```

Add the following CI/CD variables:

| Key | Value | Flags |
| --- | --- | --- |
| `SNOWFLAKE_CONNECTIONS_DEFAULT_ACCOUNT` | Your Snowflake account identifier | Protected, Masked |
| `SNOWFLAKE_CONNECTIONS_DEFAULT_USER` | Your Snowflake username | Protected |
| `SNOWFLAKE_CONNECTIONS_DEFAULT_AUTHENTICATOR` | `SNOWFLAKE_JWT` | Protected |
| `SNOWFLAKE_CONNECTIONS_DEFAULT_PRIVATE_KEY_RAW` | Private key content (PEM format) | Protected, Masked |

Then configure the pipeline:

```yaml
include:
  - component: $CI_SERVER_FQDN/snowflakedbutils/snowflake-cicd-component/configure-snowflake-cli@1.0.0
    inputs:
      default-config-file-path: "./config.toml"

stages: [build, deploy]

deploy:
  stage: deploy
  variables:
    SNOWFLAKE_CONNECTIONS_DEFAULT_AUTHENTICATOR: SNOWFLAKE_JWT
    SNOWFLAKE_CONNECTIONS_DEFAULT_PRIVATE_KEY_RAW: $PRIVATE_KEY
  script:
    - snow connection test
```

> **Note:** When using named connections, environment variables follow the format `SNOWFLAKE_CONNECTIONS_<CONNECTION_NAME>_<KEY>`. The connection name must match the name in **config.toml** (uppercased).

### Alternative: Password Authentication

Password authentication is supported but not recommended for production CI/CD. Store your password as a CI/CD variable and pass it through environment variables:

```yaml
include:
  - component: $CI_SERVER_FQDN/snowflakedbutils/snowflake-cicd-component/configure-snowflake-cli@1.0.0
    inputs:
      stage: build

stages: [build, deploy]

deploy:
  stage: deploy
  script:
    - snow connection test -x
```

<!-- ------------------------ -->
## Azure DevOps: Set Up OIDC Authentication

The Azure DevOps integration uses workload identity federation through an Azure Entra ID service connection. The setup has three parts: creating an Azure App Registration, creating an Azure DevOps service connection, and creating a Snowflake service user.

### Create an Azure App Registration with a Federated Credential

1. In the Azure Portal, go to **Microsoft Entra ID > App registrations**.
2. Click **New registration**, enter a name (e.g. `snowflake-ado-wif`), and register the application.
3. Note the **Application (client) ID** and **Directory (tenant) ID**.
4. Go to **Certificates & secrets > Federated credentials > Add credential**.
5. Select **Other issuer** and configure:
   - **Issuer:** `https://vstoken.dev.azure.com/<your-Azure-AD-Tenant-ID>`
   - **Subject identifier:** `sc://<ADO-Org-Name>/<ADO-Project-Name>/<Service-Connection-Name>`
   - **Audience:** `api://AzureADTokenExchange`

### Create an Azure DevOps Service Connection

1. In your Azure DevOps project, go to **Project Settings > Service connections**.
2. Click **New service connection > Azure Resource Manager**.
3. Select **Workload Identity federation (manual)**.
4. Fill in:
   - **Service connection name:** e.g. `snowflake-wif-connection` (this must match the subject identifier from the previous step)
   - **Subscription ID / Name:** Your Azure subscription
   - **Service Principal ID:** The Application (client) ID from the App Registration
   - **Tenant ID:** Your Azure AD Tenant ID
5. Save the connection.

### Create a Snowflake Service User

Connect to Snowflake with a user that has **ACCOUNTADMIN** or **SECURITYADMIN** privileges and run:

```sql
CREATE USER ado_cicd_user
  TYPE = SERVICE
  WORKLOAD_IDENTITY = (
    TYPE = OIDC
    ISSUER = 'https://vstoken.dev.azure.com/<Azure-AD-Tenant-ID>'
    SUBJECT = 'sc://<ADO-Org-Name>/<ADO-Project-Name>/<Service-Connection-Name>'
    OIDC_AUDIENCE_LIST = ('api://AzureADTokenExchange')
  )
  DEFAULT_ROLE = <deployment_role>;

GRANT ROLE <deployment_role> TO USER ado_cicd_user;
```

Here's what the code does:

- Creates a service user named `ado_cicd_user` that trusts OIDC tokens issued by Azure DevOps through Azure Entra ID
- The `ISSUER` incorporates your Azure AD tenant ID
- The `SUBJECT` uses the Azure DevOps service connection identifier format (`sc://<org>/<project>/<connection>`)
- The `OIDC_AUDIENCE_LIST` must be set to `api://AzureADTokenExchange`
- Grants a deployment role so the pipeline can manage Snowflake objects

The following table summarizes the claim values:

| Claim | Value | Example |
| --- | --- | --- |
| Issuer | `https://vstoken.dev.azure.com/<Azure-AD-Tenant-ID>` | `https://vstoken.dev.azure.com/72f988bf-86f1-41af-91ab-2d7cd011db47` |
| Subject | `sc://<ADO-Org>/<ADO-Project>/<Service-Connection>` | `sc://myorg/myproject/snowflake-wif-connection` |
| Audience | `api://AzureADTokenExchange` | `api://AzureADTokenExchange` |

<!-- ------------------------ -->
## Azure DevOps: Configure the Pipeline

Now let's create the Azure Pipeline that uses the Snowflake CLI Azure DevOps Extension to install the CLI and authenticate with OIDC.

### Add a Configuration File to Your Repository

Create a **config.toml** file at the root of your repository. This file contains connection metadata but no credentials:

```toml
[connections.default]
account = "<your_account>"
user = "ado_cicd_user"
warehouse = "COMPUTE_WH"
role = "<deployment_role>"
```

### Create the Pipeline

Create or update your pipeline YAML file (e.g. **azure-pipelines.yml**):

```yaml
trigger:
  - main

pool:
  vmImage: ubuntu-latest

steps:
  - task: ConfigureSnowflakeCLI@0
    inputs:
      configFilePath: './config.toml'
      cliVersion: 'latest'
      useWorkloadIdentity: true
      connectedServiceName: 'snowflake-wif-connection'
    displayName: Configure Snowflake CLI

  - script: |
      snow --version
      snow connection test
    displayName: Verify Snowflake connection

  - script: |
      snow dcm deploy --target PROD -x
    displayName: Deploy to Snowflake
```

Here's what the code does:

- Uses `ConfigureSnowflakeCLI@0` to install the Snowflake CLI and configure OIDC authentication through the Azure service connection
- Copies **config.toml** to **~/.snowflake/config.toml** with secure permissions (`0600` on Linux/macOS)
- Runs `snow connection test` to verify the connection, then `snow dcm deploy` to deploy changes

> **Note:** The `connectedServiceName` must match the service connection name you created in Azure DevOps. This is the same value used in the federated credential's subject identifier.

### Verify the Pipeline

Run the pipeline. In the pipeline logs, you should see:

- The Snowflake CLI installed successfully
- `snow connection test` returning a successful connection result

### Alternative: Key-Pair Authentication

If workload identity federation is not available, you can use key-pair authentication. Store your credentials as Azure DevOps secret variables and pass them through environment variables.

First, add the following variables to your pipeline (under **Pipelines > Library** or directly in the pipeline):

| Variable Name | Value | Secret |
| --- | --- | --- |
| `SNOWFLAKE_ACCOUNT` | Your Snowflake account identifier | Yes |
| `SNOWFLAKE_USER` | Your Snowflake username | No |
| `SNOWFLAKE_PRIVATE_KEY_RAW` | Private key content (PEM format) | Yes |
| `PASSPHRASE` | (Optional) Private key passphrase | Yes |

Then configure the pipeline:

```yaml
steps:
  - task: ConfigureSnowflakeCLI@0
    inputs:
      configFilePath: './config.toml'
      cliVersion: 'latest'
    displayName: Configure Snowflake CLI

  - script: |
      snow connection test
    env:
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_AUTHENTICATOR: 'SNOWFLAKE_JWT'
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_ACCOUNT: $(SNOWFLAKE_ACCOUNT)
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_USER: $(SNOWFLAKE_USER)
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_PRIVATE_KEY_RAW: $(SNOWFLAKE_PRIVATE_KEY_RAW)
      PRIVATE_KEY_PASSPHRASE: $(PASSPHRASE)
    displayName: Verify Snowflake connection
```

> **Note:** When using named connections, environment variables follow the format `SNOWFLAKE_CONNECTIONS_<CONNECTION_NAME>_<KEY>`. The connection name must match the name in **config.toml** (uppercased).

### Alternative: Password Authentication

Password authentication is supported but not recommended for production CI/CD:

```yaml
steps:
  - task: ConfigureSnowflakeCLI@0
    inputs:
      configFilePath: './config.toml'
      cliVersion: 'latest'
    displayName: Configure Snowflake CLI

  - script: |
      snow connection test
    env:
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_ACCOUNT: $(SNOWFLAKE_ACCOUNT)
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_USER: $(SNOWFLAKE_USER)
      SNOWFLAKE_CONNECTIONS_MYCONNECTION_PASSWORD: $(SNOWFLAKE_PASSWORD)
    displayName: Verify Snowflake connection
```

<!-- ------------------------ -->
## Troubleshooting

This section covers common issues you may encounter when setting up any of the three integrations.

### OIDC Token Generation Fails

**Symptom:** The workflow or pipeline fails when requesting an OIDC token.

**GitHub Actions resolution:**

- Verify that `permissions: id-token: write` is set in your workflow file.
- If using reusable workflows, ensure the calling workflow also passes `id-token: write`.

**GitLab CI/CD resolution:**

- Ensure `use-oidc: true` is set in the component inputs.
- If using a self-managed GitLab instance, verify OIDC token generation is enabled and the GitLab instance URL is configured as the issuer in Snowflake.

**Azure DevOps resolution:**

- Verify the `connectedServiceName` in your pipeline matches the service connection name exactly.
- Ensure the federated credential on the App Registration has the correct issuer, subject, and audience.

### OIDC Authentication Fails with Subject Mismatch

**Symptom:** Snowflake rejects the OIDC token with a claim mismatch error.

**Resolution:** Verify the `SUBJECT` in your Snowflake service user matches the actual claims in the token. You can inspect the token by adding a debug step to your pipeline:

**GitHub Actions:**

```yaml
- name: Debug OIDC claims
  run: |
    echo "$SNOWFLAKE_TOKEN" | cut -d. -f2 | \
      tr '_-' '/+' | base64 -d 2>/dev/null | \
      python3 -m json.tool
```

**GitLab CI/CD:**

```yaml
debug-oidc:
  stage: build
  script:
    - echo "$SNOWFLAKE_OIDC_TOKEN" | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | python3 -m json.tool
```

Common GitLab subject issues:
- The `project_path` in the subject includes the full group hierarchy (e.g. `mygroup/subgroup/myproject`).
- The `ref` must match the branch or tag that triggers the pipeline.

**Azure DevOps:**

```yaml
- bash: |
    echo "$SNOWFLAKE_TOKEN" | cut -d. -f2 | \
      tr '_-' '/+' | base64 -d 2>/dev/null | \
      python3 -m json.tool
  displayName: 'Debug: inspect OIDC token claims'
```

### CLI Version Not Found

**Symptom:** `uv tool install snowflake-cli==X.Y.Z` (GitHub) or `pipx install snowflake-cli==X.Y.Z` (Azure) fails with "no matching version".

**Resolution:**

- Verify the version exists on [PyPI](https://pypi.org/project/snowflake-cli/).
- For GitHub Actions, if you need a pre-release version, use `custom-github-ref` instead of `cli-version`.

### `pipx` Not Found (Azure DevOps)

**Symptom:** The `ConfigureSnowflakeCLI@0` task fails with an error about `pipx` or `PIPX_BIN_DIR`.

**Resolution:** The `ubuntu-latest` agent image includes `pipx` by default. If you're using a custom agent image, install `pipx` before the task:

```yaml
- script: pip install pipx
  displayName: Install pipx
```

### `snow` Command Not Found in Subsequent Jobs (GitLab)

**Symptom:** The `deploy` job fails with `snow: command not found`.

**Resolution:** The Snowflake CLI is installed inside the `configure-snowflake-cli` job. If your subsequent jobs run in separate containers, the CLI will not be available. Options:

1. Use `extends: .configure-snowflake-cli` to inherit the job's configuration.
2. Install the CLI directly in your job using `uv tool install snowflake-cli`.

<!-- ------------------------ -->
## Conclusion

Congratulations! You've configured Snowflake CI/CD integrations that authenticate securely with OIDC — no long-lived secrets required.

### What You Learned

- How Snowflake CI/CD integrations work: service users, OIDC authentication, and the Snowflake CLI on CI runners
- How to create a Snowflake service user with OIDC workload identity for GitHub Actions, GitLab CI/CD, and Azure DevOps
- How to configure a GitHub Actions workflow using `snowflakedb/snowflake-cli-action`
- How to configure a GitLab CI/CD pipeline using the Snowflake CI/CD Component
- How to set up an Azure Entra ID App Registration with a federated credential and configure an Azure Pipeline using `ConfigureSnowflakeCLI@0`
- How to troubleshoot common OIDC token and claim mismatch issues
- Alternative authentication methods (key-pair and password) when OIDC is not available

### Related Resources

- [Snowflake CLI GitHub Action reference](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action)
- [Snowflake CI/CD Component for GitLab reference](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/gitlab-component)
- [Snowflake CLI Azure DevOps Extension reference](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/azure-devops-extension)
- [Integrating CI/CD with Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/integrate-ci-cd)
- [DevOps with Snowflake](https://docs.snowflake.com/en/developer-guide/builders/devops-with-snowflake)
- [Snowflake Workload Identity Federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation)
- [Snowflake CLI documentation](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index)
- [snowflake-cli-action repository](https://github.com/snowflakedb/snowflake-cli-action)
- [snowflake-cicd-component repository](https://gitlab.com/snowflakedbutils/snowflake-cicd-component)
- [snowflake-ado-extension repository](https://github.com/snowflakedb/snowflake-ado-extension)
