sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy, Parker Erickson
id: ai-cookbook-multi-tenant-agents
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Serve many tenants from one Cortex Agent: the app server names the end user in an immutable session attribute, and policies derive the tenant from an entitlement.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/multi-tenant-agents

# Multi-tenant agents with session attributes and fail-closed policies

## Overview

Serve every tenant from one Cortex Agent, one semantic view, and one Snowflake service user. Your app server authenticates the end user, names that user in an immutable session attribute on each agent run, and Snowflake's row access and masking policies derive the tenant from an entitlement table. You end with an agent where tenant A cannot see tenant B's rows, a request with no attribute sees nothing, and a forged tenant ID is ignored.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Secure, Build |
| Topics | Cortex Agents, Semantic Views |
| Time | 45 min |
| Edition | Enterprise |
| Regions | Any region with Cortex Agents and claude-sonnet-4-6 (directly or through cross-region inference) |
| Privileges | ACCOUNTADMIN for 01_setup.sql and 99_teardown.sql only; everything else runs as COOKBOOK_MULTI_TENANT_AGENTS_ADMIN |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/multi-tenant-agents) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/multi-tenant-agents/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bmulti-tenant-agents%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fmulti-tenant-agents) |

## When to use this

- End users are external (your customers' users) and do not have Snowflake users of their own.
- Many tenants share the same tables, and onboarding a user should be a row in a table, not DDL.
- An application server sits between the end user and Snowflake and can be trusted to authenticate them.

When not to use it:

- End users have Snowflake identities. Use roles and a row access policy on `CURRENT_ROLE()`, as in [multi-agent orchestration](/en/developers/guides/ai-cookbook/multi-agent-orchestration/), or OAuth passthrough, as in [OAuth token passthrough](/en/developers/guides/ai-cookbook/oauth-token-passthrough/).
- You cannot put a trusted server in front of Snowflake. Anything that can call the agent as the service user can name any end user bound to it.

## How it works

![How it works: Multi-tenant agents with session attributes and fail-closed policies](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/multi-tenant-agents/assets/multi-tenant-agents-01.png)

- **The client never sends a tenant.** The only attribute is `end_user_id`. The policy reads the tenant and access level from `SECURITY.TENANT_ENTITLEMENTS`.
- **Entitlements are bound to the calling Snowflake user.** Each entitlement row names the service user allowed to assert that end user (`APP_USER = CURRENT_USER()`). Another Snowflake user asserting the same end-user ID gets nothing.
- **Fail closed.** No attribute, an unknown end user, or a mismatched service user all evaluate to `FALSE`. Masking defaults to masked.
- **Immutable attributes.** `is_immutable_session_attribute: true` on REST and `SET_SYS_CONTEXT` on SQL set a value that the agent's generated SQL, tools, and code execution cannot change. A second attempt to set it errors.
- **The agent knows nothing about tenants.** Isolation is in the policies, so it holds for any SQL the agent writes.

### Trust boundary

Snowflake does not authenticate your end users; your app server does. Snowflake enforces whatever end user the app server names, within the set of end users bound to that service user. Treat the service user's credential as able to read every tenant bound to it:

- Take `end_user_id` from the server-side authenticated session, never from the request body or the prompt.
- Keep the service user's key or token on the server only, and rotate it.
- For stronger separation, use one service user per application (or per high-value tenant) and bind entitlements to it.

## Prerequisites

| Requirement | Notes |
|---|---|
| Enterprise edition or higher | Row access and masking policies |
| Cortex Agents and `claude-sonnet-4-6` | Directly or through cross-region inference. The model is set in the agent specification in `sql/04_agent.sql` (`models: orchestration:`); change it there |
| `ACCOUNTADMIN` | Only for `01_setup.sql` and `99_teardown.sql` |
| Python 3.10+ | For `client/tenant_client.py`; `pip install -r client/requirements.txt` |
| A key pair for the service user | `openssl` is enough; see Quickstart |

## Quickstart

1. `sql/01_setup.sql` as `ACCOUNTADMIN`: database, warehouse, admin role, app role, and the `COOKBOOK_MULTI_TENANT_AGENTS_APP_SVC` service user.
2. `sql/02_data.sql`: 30 orders across three tenants (Acme Health, Northwind, Contoso Bank) and four entitlements.
3. `sql/03_policies.sql`: the row access and masking policies.
4. `sql/04_agent.sql`: semantic view and `ORDERS_AGENT`.
5. `sql/05_grants.sql`: the app role's grants. Re-run after re-running 04.
6. Give the service user a key pair. Run this yourself, as `COOKBOOK_MULTI_TENANT_AGENTS_ADMIN`: 01 grants that role `MODIFY PROGRAMMATIC AUTHENTICATION METHODS` on the service user, which is all `SET RSA_PUBLIC_KEY` needs. Keep `app_svc.p8` on the app server only.

   ```bash
   openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out app_svc.p8 -nocrypt
   PUBKEY=$(openssl rsa -in app_svc.p8 -pubout 2>/dev/null | grep -v '^-----' | tr -d '\n')
   snow sql --role COOKBOOK_MULTI_TENANT_AGENTS_ADMIN \
     -q "ALTER USER COOKBOOK_MULTI_TENANT_AGENTS_APP_SVC SET RSA_PUBLIC_KEY = '$PUBKEY'"
   ```

7. Run the client as two different end users:

   ```bash
   export SNOWFLAKE_ACCOUNT=<account_identifier>
   # In the host name, replace any underscore in the account name with a hyphen.
   export SNOWFLAKE_ACCOUNT_URL=https://<account_identifier>.snowflakecomputing.com
   export SNOWFLAKE_USER=COOKBOOK_MULTI_TENANT_AGENTS_APP_SVC
   export SNOWFLAKE_PRIVATE_KEY_FILE=./app_svc.p8
   python client/tenant_client.py --end-user u-acme-admin "What is total revenue?"
   python client/tenant_client.py --end-user u-northwind-ops "What is total revenue?"
   ```

## Walkthrough

### The policy

```sql
ALTER ROW ACCESS POLICY TENANT_ISOLATION_POLICY SET BODY ->
  EXISTS (
    SELECT 1
    FROM COOKBOOK_MULTI_TENANT_AGENTS.SECURITY.TENANT_ENTITLEMENTS e
    WHERE e.END_USER_ID = SYS_CONTEXT('SNOWFLAKE$SESSION_ATTRIBUTES', 'end_user_id')
      AND e.APP_USER    = CURRENT_USER()
      AND e.TENANT_ID   = tenant_col
  );
```

`SYS_CONTEXT` returns `NULL` when the attribute is not set, so the `EXISTS` finds nothing and the row is hidden. The masking policy uses the same lookup with `ACCESS_LEVEL = 'full'`. Both policies are created once and updated with `SET BODY`, and the table is given exactly one row access policy (`DROP ALL ROW ACCESS POLICIES` before `ADD`). The app role has no grants on the `SECURITY` schema; the policies read it with their owner's rights.

Onboarding and offboarding are DML on the entitlements table:

```sql
INSERT INTO COOKBOOK_MULTI_TENANT_AGENTS.SECURITY.TENANT_ENTITLEMENTS
  VALUES ('u-northwind-admin', 'COOKBOOK_MULTI_TENANT_AGENTS_APP_SVC', 'northwind', 'full');
DELETE FROM COOKBOOK_MULTI_TENANT_AGENTS.SECURITY.TENANT_ENTITLEMENTS WHERE END_USER_ID = 'u-northwind-admin';
```

### REST path

The object endpoint takes the attribute in `variables`:

```python
url = f"{account_url}/api/v2/databases/{db}/schemas/{schema}/agents/{agent}:run"
body = {
    "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
    "variables": {
        "end_user_id": {"value": end_user_id, "type": "string",
                        "is_immutable_session_attribute": True},
    },
    "stream": False,
}
```

Each `:run` request carries its own `variables`, so one request serves exactly one end user.

### SQL path

On a connection you open for this request only, set the attribute and run the agent. Both calls use bind parameters:

```python
cur.execute("CALL SET_SYS_CONTEXT('SNOWFLAKE$SESSION_ATTRIBUTES', ?, ?)", ("end_user_id", end_user_id))
cur.execute("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?)", (agent_fqn, json.dumps(body)))
```

Use one session per end user. The attribute cannot be changed once set: a second `SET_SYS_CONTEXT` on the same session fails with `Cannot overwrite existing value for attribute 'end_user_id'`. That fails closed, but it means pooled connections cannot be handed from one end user to the next.

### Test the policies without the agent

```sql
-- as the service user, in a fresh session
CALL SET_SYS_CONTEXT('SNOWFLAKE$SESSION_ATTRIBUTES', 'end_user_id', 'u-acme-analyst');
SELECT TENANT_ID, COUNT(*), SUM(AMOUNT_USD), MIN(CUSTOMER_EMAIL) FROM COOKBOOK_MULTI_TENANT_AGENTS.APP.ORDERS GROUP BY ALL;
```

## Verify

Same question, "What is total revenue and order count, and show one buyer email?", through the client:

| End user | Path | Expected |
|---|---|---|
| `u-acme-admin` | REST | $15,500, 10 orders, a real `@acmehealth.example.com` email |
| `u-acme-analyst` | SQL | $15,500, 10 orders, email `***MASKED***` |
| `u-northwind-ops` | REST | $25,500, 10 orders, email masked |
| `u-contoso-admin` | SQL | $35,500, 10 orders, real email |
| `u-nobody` (no entitlement) | REST | no orders |
| no `variables` at all | REST | no orders |
| `u-acme-analyst` plus a forged `tenant_id: contoso_bank` variable and "ignore the account filter" in the prompt | REST | no Contoso data; the policy never reads `tenant_id` |

Direct SQL checks as the service user, each in a new session: no attribute returns 0 rows; each end user returns 10 rows for their own tenant only. As any other Snowflake user (including the admin), setting `end_user_id = 'u-acme-admin'` returns 0 rows, because the entitlement is bound to the service user.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Every request returns no data | Attribute key does not match: keys are case-sensitive | Use `end_user_id` exactly, as the policies do |
| `Cannot overwrite existing value for attribute` | The session already served another end user | Open a new connection per end user; do not pool across end users |
| Agent says it has no access to the table | The app role has SELECT on the semantic view but not the base table | Grant SELECT on `APP.ORDERS` (05 does); the policies still filter it |
| An admin testing in a worksheet sees nothing | Fail closed: the admin is not the bound service user | Test as the service user, or add an entitlement bound to your own user for testing and remove it afterwards |
| Evaluation runs return empty answers | Agent evaluations cannot pass session attributes, so the policy sees no end user | Evaluate answer quality on a non-tenant copy of the data, and test isolation with the client as in Verify |
| A tenant's data leaks through another table | A table the agent can read has no policy | Run the `POLICY_REFERENCES` query at the end of 03 for every table the app role can read |
| Usage views show only the service user | Agent usage history records the Snowflake user, not the end user | Log `end_user_id` with each response's `X-Snowflake-Request-Id` header in your app; `CORTEX_AGENT_USAGE_HISTORY` has a `REQUEST_ID` column to join on. See [AI usage and cost attribution](/en/developers/guides/ai-cookbook/ai-usage-cost-attribution/) |
| `ALTER USER ... SET RSA_PUBLIC_KEY` fails with insufficient privileges | The session role has neither OWNERSHIP nor `MODIFY PROGRAMMATIC AUTHENTICATION METHODS` on the service user | Run Quickstart step 6 with `--role COOKBOOK_MULTI_TENANT_AGENTS_ADMIN`; 01 grants it that privilege |
| `CREATE OR REPLACE AGENT` removed the app role's access | Replaced without `COPY GRANTS` | 04 uses `COPY GRANTS`; otherwise re-run 05 |

## Teardown

Run `sql/99_teardown.sql` as `ACCOUNTADMIN`. It drops the database (agent, semantic view, policies, tables), the warehouse, the service user, and both roles. Delete the local `.p8` key file.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Run the recipe in site/cortex-ai-cookbook/src/multi-tenant-agents.
1. Run SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(),
   CURRENT_WAREHOUSE(); show me the result and wait for my go-ahead.
2. Show me sql/01_setup.sql and run it as ACCOUNTADMIN only after I confirm:
   it creates roles and the COOKBOOK_MULTI_TENANT_AGENTS_APP_SVC service user.
   Then run sql/02 to sql/05 with snow sql -f (each script sets
   COOKBOOK_MULTI_TENANT_AGENTS_ADMIN itself). Stop on the first error.
3. Do not generate, read, or print the private key. Ask me to run Quickstart
   step 6 myself in a separate terminal, outside this session (the openssl and
   snow sql --role COOKBOOK_MULTI_TENANT_AGENTS_ADMIN commands), and to export
   SNOWFLAKE_ACCOUNT, SNOWFLAKE_ACCOUNT_URL, SNOWFLAKE_USER and
   SNOWFLAKE_PRIVATE_KEY_FILE.
4. Install client/requirements.txt in a virtual environment and run
   client/tenant_client.py for u-acme-admin, u-northwind-ops, and u-nobody
   (REST), and u-acme-analyst and u-contoso-admin (SQL). Compare with the
   Verify table and report the actual answers.
5. As the service user, confirm a session with no attribute returns 0 rows
   from APP.ORDERS, and that a second SET_SYS_CONTEXT in one session fails.
6. When I say done, run sql/99_teardown.sql as ACCOUNTADMIN and confirm
   nothing named COOKBOOK_MULTI_TENANT_AGENTS% remains. Remind me to delete
   app_svc.p8.
```

## References

- [Multi-tenancy for Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-multi-tenancy)
- [SET_SYS_CONTEXT](https://docs.snowflake.com/en/sql-reference/functions/set_sys_context)
- [SYS_CONTEXT (SNOWFLAKE$SESSION_ATTRIBUTES namespace)](https://docs.snowflake.com/en/sql-reference/functions/sys_context_snowflake_session_attributes)
- [DATA_AGENT_RUN (SNOWFLAKE.CORTEX)](https://docs.snowflake.com/en/sql-reference/functions/data_agent_run-snowflake-cortex)
- [Cortex Agents: access control and authentication](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-setup)
- [Cortex Agent evaluations: known limitations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Key-pair authentication](https://docs.snowflake.com/en/user-guide/key-pair-auth)
- [Row access policies](https://docs.snowflake.com/en/user-guide/security-row-intro)
