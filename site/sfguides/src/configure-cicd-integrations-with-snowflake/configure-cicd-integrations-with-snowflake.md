author: Gilberto Hernandez, Oskar Lorek
id: configure-cicd-integrations-with-snowflake
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/data-engineering, snowflake-site:taxonomy/product/platform
language: en
summary: Configure the Snowflake CLI GitHub Action in your CI/CD pipeline with OIDC authentication.
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Configure CI/CD Integrations with Snowflake

<!-- ------------------------ -->
## Overview

CI/CD pipelines let you automate Snowflake deployments so that changes are triggered by pull requests, merges, or scheduled runs rather than manual steps. Snowflake publishes first-party integrations for the most popular CI/CD platforms, each of which installs the Snowflake CLI on the runner and configures authentication to your Snowflake account.

In this Quickstart, we'll walk through configuring the [Snowflake CLI GitHub Action](https://github.com/snowflakedb/snowflake-cli-action) (`snowflakedb/snowflake-cli-action`). This integration supports workload identity federation (WIF) with OpenID Connect (OIDC), which means your pipeline can authenticate to Snowflake with short-lived tokens instead of long-lived secrets. We'll focus on OIDC as the recommended approach and cover key-pair and password alternatives briefly.

### What You'll Learn

- How Snowflake CI/CD integrations work at a high level
- How to create a Snowflake service user with OIDC workload identity for GitHub Actions
- How to configure a GitHub Actions workflow that authenticates to Snowflake
- How to troubleshoot common OIDC authentication issues

### What You'll Need

- A [Snowflake account](https://signup.snowflake.com/)
- A Snowflake user with **ACCOUNTADMIN** or **SECURITYADMIN** privileges
- A GitHub repository with GitHub Actions enabled
- Snowflake CLI version 3.11 or later (for OIDC authentication)

### What You'll Build

- A GitHub Actions workflow that installs the Snowflake CLI, authenticates via OIDC, and runs Snowflake CLI commands

<!-- ------------------------ -->
## How Snowflake CI/CD Integrations Work

Before diving into platform-specific configuration, let's look at the concepts that are shared across all Snowflake CI/CD integrations.

### Service Users

Every CI/CD pipeline authenticates to Snowflake as a **service user** — a non-human user created specifically for automation. You create this user in Snowflake with `TYPE = SERVICE` and grant it only the roles the pipeline needs.

### Authentication with OIDC

Snowflake recommends workload identity federation (WIF) with OIDC for CI/CD. Here's how it works:

1. The CI runner requests a short-lived identity token from the platform's OIDC provider (GitHub, Azure Entra ID, etc.).
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
## Troubleshooting

This section covers common issues you may encounter when setting up the GitHub Actions integration.

### OIDC Token Generation Fails

**Symptom:** The workflow fails when requesting an OIDC token.

**Resolution:**

- Verify that `permissions: id-token: write` is set in your workflow file.
- If using reusable workflows, ensure the calling workflow also passes `id-token: write`.

### OIDC Authentication Fails with Subject Mismatch

**Symptom:** Snowflake rejects the OIDC token with a claim mismatch error.

**Resolution:** Verify the `SUBJECT` in your Snowflake service user matches the actual claims in the token. You can inspect the token by adding a debug step to your workflow:

```yaml
- name: Debug OIDC claims
  run: |
    echo "$SNOWFLAKE_TOKEN" | cut -d. -f2 | \
      tr '_-' '/+' | base64 -d 2>/dev/null | \
      python3 -m json.tool
```

### CLI Version Not Found

**Symptom:** `uv tool install snowflake-cli==X.Y.Z` fails with "no matching version".

**Resolution:**

- Verify the version exists on [PyPI](https://pypi.org/project/snowflake-cli/).
- If you need a pre-release version, use `custom-github-ref` instead of `cli-version`.

<!-- ------------------------ -->
## Conclusion

Congratulations! You've configured the Snowflake CLI GitHub Action to authenticate securely with OIDC — no long-lived secrets required.

### What You Learned

- How Snowflake CI/CD integrations work: service users, OIDC authentication, and the Snowflake CLI on CI runners
- How to create a Snowflake service user with OIDC workload identity for GitHub Actions
- How to configure a GitHub Actions workflow using `snowflakedb/snowflake-cli-action`
- How to troubleshoot common OIDC token and claim mismatch issues
- Alternative authentication methods (key-pair and password) when OIDC is not available

### Related Resources

- [Snowflake CLI GitHub Action reference](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/github-action)
- [Integrating CI/CD with Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/cicd/integrate-ci-cd)
- [DevOps with Snowflake](https://docs.snowflake.com/en/developer-guide/builders/devops-with-snowflake)
- [Snowflake Workload Identity Federation](https://docs.snowflake.com/en/user-guide/workload-identity-federation)
- [Snowflake CLI documentation](https://docs.snowflake.com/en/developer-guide/snowflake-cli/index)
- [snowflake-cli-action repository](https://github.com/snowflakedb/snowflake-cli-action)
