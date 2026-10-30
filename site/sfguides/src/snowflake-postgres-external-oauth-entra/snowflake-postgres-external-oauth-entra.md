id: snowflake-postgres-external-oauth-entra
summary: Configure External OAuth authentication for Snowflake Postgres using Microsoft Entra ID
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform, snowflake-site:taxonomy/snowflake-feature/postgres
language: en
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfquickstarts/issues
authors: Elizabeth Christensen
fork repo link: https://github.com/Snowflake-Labs/sfquickstarts/tree/master/site/sfguides/src/snowflake-postgres-external-oauth-entra
tags: Postgres

# Configure External OAuth for Snowflake Postgres with Microsoft Entra ID
<!-- ------------------------ -->
## Overview

In this guide, you'll configure a Snowflake Postgres instance to authenticate connections using OAuth 2.0 access tokens issued by Microsoft Entra ID (formerly Azure AD). Instead of managing Postgres passwords directly, clients present a JWT from your identity provider to connect.

### What is External OAuth for Snowflake Postgres?

External OAuth authentication lets connections to a Snowflake Postgres instance use OAuth 2.0 access tokens (JSON Web Tokens, or JWTs) issued by a third-party identity provider. When configured, the Postgres instance validates incoming JWTs against the IdP's published keys before allowing a connection.

### Two authentication patterns

This guide covers two authentication patterns that can be configured simultaneously on the same instance:

| Pattern | Auth Flow | Entra Credential | JWT Claim Used | Use Case |
|---------|-----------|------------------|----------------|----------|
| Application user | Client credentials | Client secret | `appid` in `roles` claim | Service accounts, scripts, apps |
| Human user | Delegated (auth code) | User login (interactive) | `email` in `scp` claim | End users authenticating as themselves |

### What You'll Need

- A running Snowflake Postgres instance ([Getting Started with Snowflake Postgres](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-postgres/))
- A Snowflake role with OWNERSHIP or MODIFY privilege on the Postgres instance
- A Microsoft Entra ID tenant where you have the Application Administrator or Global Administrator role
- psql or another Postgres client installed locally
- curl (for testing token retrieval)

### What You'll Learn

- How to register a resource app and a client app in Microsoft Entra ID
- How to configure app roles (for service accounts) and scopes (for human users)
- How to set the External OAuth authentication authority on a Postgres instance with multiple accepted token patterns
- How to map Postgres users to JWT claims
- How to obtain tokens and connect using both flows

### What You'll Build

- A working External OAuth integration between Microsoft Entra ID and Snowflake Postgres, supporting both application (client credentials) and human (delegated) authentication flows.

<!-- ------------------------ -->
## Register the Resource App

You need two app registrations in Entra ID:

- A resource app — represents the Postgres instance (the thing that accepts tokens). Its App ID becomes the `audience` in JWTs.
- A client app — represents the application or user requesting tokens.

Start by creating the resource app.

1. Navigate to the [Azure Portal](https://portal.azure.com) and sign in.
2. Search for **Microsoft Entra ID** in the top search bar and select it.
3. In the left sidebar, select **App registrations**.
4. Select **+ New registration**.
5. Fill in the registration form:
   - **Name**: `Snowflake Postgres OAuth Resource` (or any descriptive name)
   - **Supported account types**: Select "Accounts in this organizational directory only" (single tenant)
   - **Redirect URI**: Leave blank
6. Select **Register**.

After registration, note the **Application (client) ID** from the **Overview** page — this is your `RESOURCE_APP_ID`. You'll also need the **Directory (tenant) ID**.

<!-- ------------------------ -->
## Configure the Resource App

The resource app needs both an app role (for the client credentials/application flow) and a scope (for the delegated/human flow).

### Add an App Role (for application flow)

1. In the resource app, select **App roles** in the left menu.
2. Select **Create app role**.
3. Fill in:
   - **Display name**: `Postgres.Login.Role`
   - **Allowed member types**: **Applications**
   - **Value**: `Postgres.Login.Role`
   - **Description**: `Allows client credential access to Snowflake Postgres`
4. Select **Apply**.

### Expose an API and add a scope (for delegated/human flow)

1. In the left menu, select **Expose an API**.
2. Next to **Application ID URI**, select **Set**. Accept the default value (`api://<RESOURCE_APP_ID>`) or set a custom URI. Select **Save**.
3. Under **Scopes defined by this application**, select **+ Add a scope**.
4. Fill in:
   - **Scope name**: `postgres.login.scope`
   - **Who can consent**: Admins and users
   - **Admin consent display name**: Access Snowflake Postgres
   - **Admin consent description**: Allows delegated access to Snowflake Postgres
5. Select **Add scope**.

Record these values:

| Value | Where to find it | Used as |
|-------|------------------|---------|
| Resource App ID | Overview page of resource app | Part of `AUDIENCE` |
| Application ID URI | Expose an API page (for example, `api://<RESOURCE_APP_ID>`) | `AUDIENCE` |
| Scope name | Expose an API > Scopes (`postgres.login.scope`; the full string `api://<RESOURCE_APP_ID>/postgres.login.scope` is what clients request) | `SCOPES` for delegated flow |
| App role value | App roles page (`Postgres.Login.Role`) | `SCOPES` for application flow |
| Tenant ID | Overview page | Part of `ISSUER` URL |

### Add the email optional claim (for delegated/human flow)

Entra v1 access tokens don't include the `email` claim by default. Add it to the resource app so the delegated token carries the value Postgres maps on:

1. In the resource app, select **Token configuration** in the left menu.
2. Select **+ Add optional claim**.
3. For **Token type**, select **Access**.
4. Check `email` and select **Add**.
5. If prompted, check **Turn on the Microsoft Graph email permission** and select **Add**.

> The `email` claim is only populated when the user has an email address set in Entra ID.

<!-- ------------------------ -->
## Configure the Client App

Now register (or use an existing) client app — the app that will request tokens.

1. In **App registrations**, select **+ New registration** (or select your existing client app).
2. Name: `Snowflake Postgres OAuth Client` (or similar).
3. Supported account types: **Accounts in this organizational directory only**.
4. Select **Register**.
5. Note the **Application (client) ID** — this is your `CLIENT_APP_ID`.

### Create a client secret

1. In the client app, select **Certificates & secrets** in the left menu.
2. Select **+ New client secret**.
3. Add a description (for example, `postgres-oauth`) and select an expiration period.
4. Select **Add**.
5. Copy the secret value immediately — it only displays once.

### Grant API permissions to the resource app

> Tip: Start with the App Role (application/client credentials flow) first — it's the easiest to test with a single `curl` command. You can add the delegated scope for human users afterward.

1. In the client app, select **API permissions** > **Add a permission**.
2. Select **My APIs** and look for your resource app. If it doesn't appear there, search by the resource app's Application (client) ID in the search box, or check the **APIs my organization uses** tab.
3. **Add the App Role (for application flow):**
   - Select **Application permissions**
   - Check `Postgres.Login.Role`
   - Select **Add permissions**
4. **Add the Scope (for delegated/human flow):**
   - Select **Add a permission** again > **My APIs** > resource app
   - Select **Delegated permissions**
   - Check `postgres.login.scope`
   - Select **Add permissions**
5. On the following screen, select **Grant admin consent for [your tenant]** > **Yes**.

Both permissions should now show as **Granted** with a green checkmark.

### Add a redirect URI (required for delegated flow only)

If you plan to use the delegated/human flow:

1. In the client app, select **Authentication** > **Add a platform** > **Web**.
2. Redirect URI: `http://localhost:8000/callback` (for local testing).
3. Select **Configure**.

> If you only need the application/client credentials flow, you can skip this step.

<!-- ------------------------ -->
## Configure the Snowflake Postgres Instance

Now configure your Snowflake Postgres instance to accept tokens from Entra ID. Run the following SQL in a Snowflake worksheet or using the Snowflake CLI.

Replace the placeholder values with the ones you recorded:

```sql
ALTER POSTGRES INSTANCE my_postgres_instance SET
  AUTHENTICATION_AUTHORITY = EXTERNAL_OAUTH
  AUTHENTICATION_PROPERTIES = (
    ISSUER = 'https://sts.windows.net/<tenant-id>/',
    AUDIENCE = 'api://<RESOURCE_APP_ID>',
    ACCEPTED_TOKENS = (
      -- Human/delegated flow: identity from 'email' claim, scope in 'scp' claim
      (MAPPING_CLAIM = 'email', SCOPES = ('postgres.login.scope')),

      -- Application/client credentials flow: identity from 'appid' claim, scope in 'roles' claim
      (MAPPING_CLAIM = 'appid', SCOPES_CLAIM = 'roles', SCOPES = ('Postgres.Login.Role'))
    )
  );
```

### Property reference

| Field | Description |
|-------|-------------|
| `ISSUER` | Must exactly match the `iss` claim in the JWT, including trailing slash. See the note below on v1 vs v2 endpoints. |
| `AUDIENCE` | Must exactly match the `aud` claim in the JWT. Use the Application ID URI from the resource app. |
| `MAPPING_CLAIM` | Which JWT claim holds the identity to match against `OAUTH_IDENTIFIER` on the Postgres user. |
| `SCOPES_CLAIM` | Which JWT field holds the granted scopes/roles. Defaults to `scp` if omitted. Set to `roles` for client credentials tokens. |
| `SCOPES` | The specific scope/role value that must be present in the token. |

> Important: v1 vs v2 token endpoints and the ISSUER value
>
> The issuer (`iss`) in the JWT depends on which token endpoint you call:
>
> | Endpoint | URL | `iss` claim in JWT |
> |----------|-----|--------------------|
> | v1 | `https://login.microsoftonline.com/<tenant-id>/oauth2/token` | `https://sts.windows.net/<tenant-id>/` |
> | v2 | `https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token` | `https://login.microsoftonline.com/<tenant-id>/v2.0` |
>
> The `ISSUER` in your Postgres configuration must match exactly — including the trailing slash for v1. This guide uses the v1 endpoint.

For the full property reference, see [Configure authentication for Snowflake Postgres](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-authentication).

<!-- ------------------------ -->
## Map Users to Claims

Connect to your Postgres instance with existing credentials (for example, the `snowflake_admin` user):

```bash
psql postgres://snowflake_admin:****@<host>:5432/postgres
```

### Create the application user

The application user maps to your client app. The `oauth_identifier` must match the `appid` claim value from the JWT (the client app's Application ID).

```sql
-- Create the user
CREATE USER app_user;

-- Map to the client app's appid from the JWT
ALTER ROLE app_user SET oauth_identifier = '<CLIENT_APP_ID>';

-- Grant necessary database privileges
GRANT CONNECT ON DATABASE my_database TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_user;
```

### Create a human user

The human user maps to a real person. The `oauth_identifier` must match the `email` claim in their delegated JWT.

```sql
-- Create the user
CREATE USER jane_smith;

-- Map to the user's email address (must match 'email' claim in the JWT)
ALTER ROLE jane_smith SET oauth_identifier = 'jane.smith@example.com';

-- Grant privileges
GRANT CONNECT ON DATABASE my_database TO jane_smith;
GRANT USAGE ON SCHEMA public TO jane_smith;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO jane_smith;
```

> Note: Setting `oauth_identifier` on a user places them in the `snowflake_oauthin` group, routing them through token authentication instead of password authentication. After this, that user can no longer authenticate with a password.

<!-- ------------------------ -->
## Get a Token and Connect

### Test application flow (client credentials)

Request a token using the v1 endpoint:

```bash
TOKEN=$(curl -s -X POST \
  "https://login.microsoftonline.com/<tenant-id>/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=<CLIENT_APP_ID>" \
  -d "client_secret=<client-secret>" \
  -d "resource=api://<RESOURCE_APP_ID>" \
  -d "grant_type=client_credentials" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### Decode and verify the token

Paste the token into [jwt.ms](https://jwt.ms) to decode it. Verify that:

- `iss` = `https://sts.windows.net/<tenant-id>/` (matches your `ISSUER`)
- `aud` = `api://<RESOURCE_APP_ID>` (matches your `AUDIENCE`)
- `appid` = `<CLIENT_APP_ID>` (this becomes the `OAUTH_IDENTIFIER` for the app user)
- `roles` contains `Postgres.Login.Role`

### Connect with psql (application user)

```bash
PGPASSWORD="$TOKEN" psql \
  -h <your-instance-host>.postgres.snowflake.app \
  -p 5432 \
  -U app_user \
  -d my_database
```

### Test human/delegated flow

The delegated flow requires an interactive browser login. You can use a local Flask app, Postman, or any tool that implements the [authorization code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow) to obtain a delegated token. Once you have a token:

```bash
PGPASSWORD="<delegated_access_token>" psql \
  -h <your-instance-host>.postgres.snowflake.app \
  -p 5432 \
  -U jane_smith \
  -d my_database
```

If the connection succeeds, External OAuth is working. The Postgres instance validated the JWT signature, checked the issuer, audience, and scopes, and matched the mapping claim to the user's `oauth_identifier`.

<!-- ------------------------ -->
## Clean Up

If you created these resources only for this guide, remove them when you're done.

### Drop the Postgres roles

Connect to `my_database` as `snowflake_admin`, then revoke the roles' privileges and drop them:

```sql
DROP OWNED BY app_user, jane_smith;
DROP ROLE app_user;
DROP ROLE jane_smith;
```

### Revert the instance's authentication settings

Run the following in Snowflake to return the instance to Postgres authentication. Setting `AUTHENTICATION_PROPERTIES` to `NULL` removes the stored issuer, audience, and accepted tokens.

```sql
ALTER POSTGRES INSTANCE my_postgres_instance SET
  AUTHENTICATION_AUTHORITY = POSTGRES
  AUTHENTICATION_PROPERTIES = NULL;
```

> Switching to External OAuth revoked the `application` role's password. After you revert, run `ALTER POSTGRES INSTANCE my_postgres_instance RESET ACCESS FOR 'application';` if your apps need it.

### Delete the Entra ID resources

1. In the [Azure Portal](https://portal.azure.com), go to **Microsoft Entra ID** > **App registrations**.
2. Select the client app, then select **Certificates & secrets** and delete the `postgres-oauth` client secret.
3. On the client app's **Overview** page, select **Delete** and confirm.
4. Select the resource app, then select **Delete** on its **Overview** page and confirm.

<!-- ------------------------ -->
## Conclusion and Resources

You've configured External OAuth authentication for Snowflake Postgres using Microsoft Entra ID, supporting both application and human user flows.

### What You Learned

- How to register a resource app and client app in Microsoft Entra ID with app roles and scopes
- How to configure a Snowflake Postgres instance with the `EXTERNAL_OAUTH` authentication authority and multiple `ACCEPTED_TOKENS` entries
- How to map Postgres users to JWT claims with `oauth_identifier`
- How to obtain tokens using both the client credentials flow and delegated flow, and connect to Postgres
- The difference between v1 and v2 token endpoints and how they affect the `ISSUER` value

### Related Resources

- [Snowflake Postgres Authentication Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/postgres-authentication)
- [Snowflake Postgres Documentation](https://docs.snowflake.com/en/user-guide/snowflake-postgres/about)
- [Getting Started with Snowflake Postgres Quickstart](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-postgres/)
- [Microsoft Entra ID: Register an application](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- [Microsoft Entra ID: Client credentials flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow)
- [Microsoft Entra ID: Expose a web API](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-configure-app-expose-web-apis)
- [Microsoft Entra ID: App roles](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps)
