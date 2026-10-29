sidebar: true
sidebar_json: ai-cookbook
author: Parker Erickson
id: ai-cookbook-agent-versioning-and-promotion
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Commit, alias, promote, A/B route, and roll back Cortex Agent versions with runnable SQL and the behaviors observed along the way.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/recipes/cortex-agents/agent-versioning-and-promotion

# Agent versioning and promotion

## Overview

Run a Cortex Agent the way you run any production service: develop on a mutable
LIVE version, freeze it into an immutable named version, point a PRODUCTION alias
at the version you trust, send a slice of traffic to a CANARY alias, and promote
or roll back by moving the alias. Applications never change the version they
call. They call `!PRODUCTION`, and you decide what that means.

## When to use this

- An agent has users, and edits to its instructions or tools must not reach them
  until someone has tested the change.
- You want a one-statement rollback to a configuration that is known to work.
- You deploy agent specs from Git and need an import path that does not involve
  editing the agent by hand.
- You want to compare two versions on real traffic before switching.

When not to use it:

- A throwaway prototype that only you call. Edit LIVE and move on.
- Temporary agents. They run on LIVE only; COMMIT, `VERSION$N`, aliases, and
  `SHOW VERSIONS IN AGENT` are not supported for them.

## How it works

![Versioning flow: create an agent, commit a version, alias it LIVE, then promote or roll back](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/991c25b49527b1f22e5d8678baba2b3ddeb795bf/journeys/ai-cookbook/agent-versioning-and-promotion/assets/agent-versioning-and-promotion.png)


Key concepts:

1. **LIVE and named versions.** Each agent has at most one LIVE version, the only
   one you can edit. `COMMIT` freezes LIVE into the next `VERSION$N` and consumes
   it; you add a new LIVE with `ADD LIVE VERSION FROM LAST` when you resume work.
   Named versions cannot change, only their comment and alias can.
2. **Version identifiers.** A version is referenced by its system name
   (`VERSION$N`), by a user-defined alias, or by one of four shortcuts:
   `LIVE` (the live version), `FIRST` (the first committed named version), `LAST`
   (the most recently committed named version), and `DEFAULT` (the version set as
   the agent's default). The same identifiers work in the REST path
   `/agents/{name}/versions/{version}:run`, in the `DATA_AGENT_RUN` suffix
   `'db.schema.agent!<version>'`, in stage URIs, and in an evaluation's
   `agent_version`.
3. **DEFAULT is what unversioned callers get.** Unless you set it, DEFAULT is the
   latest committed version, so every commit changes it. Pin it with
   `SET DEFAULT_VERSION = 'VERSION$N'` and move it on purpose.
4. **Aliases are pointers.** Promotion and rollback are metadata-only alias
   moves. Callers keep calling the same alias and get the new version on their
   next request.
5. **Traffic splitting is the caller's job.** Snowflake does not split traffic
   between versions. The application picks an alias per request; this recipe does
   it in a caller's-rights procedure that buckets a stable routing key.

## Prerequisites

| Requirement | Notes |
|---|---|
| Cortex Agents available in your account | The agent names `auto` as its orchestration model |
| `ACCOUNTADMIN` for `01_setup.sql` and `99_teardown.sql` | 01 creates the recipe role, warehouse, and database, and grants `SNOWFLAKE.CORTEX_USER` to the role. Teardown drops them. Scripts 02 to 07 run as `COOKBOOK_AGENT_VERSIONING_AND_PROMOTION_ADMIN`. |
| A SQL client | Snowsight worksheets or `snow sql -f`. Run files in order. |
| Default role and warehouse | Cortex Agents authorize a run against the caller's default role and need a default warehouse. With `DEFAULT_SECONDARY_ROLES = ('ALL')` the recipe role is available after it is granted to you. |

## Quickstart

1. `sql/01_setup.sql`: role, warehouse, database, the agent (VERSION$1 plus
   LIVE), DEFAULT pinned to VERSION$1, PRODUCTION on VERSION$1.
2. `sql/02_commit_candidate.sql`: edit LIVE, commit VERSION$2, point CANARY at
   it, add a new LIVE.
3. `sql/03_route_by_version.sql`: ask every reference the same question and read
   the version tag in each answer.
4. `sql/04_ab_routing.sql`: route four requests through a 50/50 CANARY split and
   look at the log.
5. `sql/05_promote.sql`: move PRODUCTION and DEFAULT to the CANARY version.
6. `sql/06_rollback.sql`: move them back to the previous PRODUCTION version.
7. `sql/07_import_version_from_stage.sql`: create a version from a spec file on a
   stage, the CI/CD path.
8. `sql/99_teardown.sql`: remove everything.

The agent's response instruction makes every answer start with a tag such as
`[v2]`, so you can see which version served a request without opening traces.

## Walkthrough

### Commit a candidate

Edit LIVE, then commit. `MODIFY LIVE VERSION SET SPECIFICATION` replaces the
whole spec, so always send the complete spec.

```sql
ALTER AGENT RELEASE_AGENT MODIFY LIVE VERSION SET SPECIFICATION = $$ ... $$;
ALTER AGENT RELEASE_AGENT COMMIT COMMENT = 'v2 candidate: new response instructions';
ALTER AGENT RELEASE_AGENT ADD LIVE VERSION FROM LAST COMMENT = 'Next iteration';
```

`ADD LIVE VERSION` fails with "There is already a live version. Please commit it
first." when LIVE exists, so `02` checks `SHOW VERSIONS IN AGENT` first and only
adds LIVE when it is missing.

### Aliases and the default

```sql
ALTER AGENT RELEASE_AGENT SET DEFAULT_VERSION = 'VERSION$1';
ALTER AGENT RELEASE_AGENT MODIFY VERSION VERSION$1 SET ALIAS = production;
ALTER AGENT RELEASE_AGENT MODIFY VERSION VERSION$2 SET ALIAS = canary;
```

`MODIFY VERSION` needs a system name; `MODIFY VERSION LAST ...` is a syntax
error. The scripts read the name they need from `DESCRIBE AGENT`, whose `aliases`
column maps every alias and shortcut to a `VERSION$N`, and check it against
`^VERSION\$[0-9]+$` before using it in a statement.

### Route by alias

```sql
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
  'COOKBOOK_AGENT_VERSIONING_AND_PROMOTION.AGENTS.RELEASE_AGENT!PRODUCTION',
  $${"messages":[{"role":"user","content":[{"type":"text","text":"Say hello."}]}]}$$);
```

Unquoted aliases are stored in uppercase, and the suffix is matched as written:
`!PRODUCTION` works and `!production` returns error 399535, "Version not found".
`!version$1` and `!VERSION$1` both work.

### A/B routing

`04_ab_routing.sql` creates `ASK_WITH_AB_ROUTING(routing_key, question,
canary_percent)`. It hashes the key into a bucket from 0 to 99, sends the request
to CANARY when the bucket is below `canary_percent` and to PRODUCTION otherwise,
and logs the bucket, the alias, and the answer. The same key always lands in the
same bucket, so a user sees one version consistently.

```sql
bucket := MOD(ABS(HASH(:ROUTING_KEY)), 100);
IF (bucket < CANARY_PERCENT) THEN
  raw := (SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('...RELEASE_AGENT!CANARY', :body));
ELSE
  raw := (SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN('...RELEASE_AGENT!PRODUCTION', :body));
END IF;
```

The agent argument of `DATA_AGENT_RUN` must be a constant (a literal or a session
variable); a column expression fails to compile. Choosing between two literal
references also works as an allowlist: no input can route to another agent or
version. The request body is built with `OBJECT_CONSTRUCT`, never by
concatenating the question into JSON. The procedure is `EXECUTE AS CALLER`, so
the agent runs with the caller's privileges.

In an application that calls the REST API, the same logic picks the version path
segment:

```python
import hashlib

def pick_alias(routing_key: str, canary_percent: int) -> str:
    bucket = int(hashlib.sha256(routing_key.encode()).hexdigest(), 16) % 100
    return "CANARY" if bucket < canary_percent else "PRODUCTION"

# POST {account_url}/api/v2/databases/{db}/schemas/{schema}/agents/{agent}/versions/{alias}:run
# body: {"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]}
```

Log the alias with every request so feedback, evaluation scores, and latency can
be compared per version.

### Promote and roll back

`05_promote.sql` records the current PRODUCTION version in `PROMOTION_LOG`,
moves PRODUCTION to the CANARY version, and pins DEFAULT to it:

```sql
ALTER AGENT RELEASE_AGENT MODIFY VERSION VERSION$2 SET ALIAS = production;
ALTER AGENT RELEASE_AGENT SET DEFAULT_VERSION = 'VERSION$2';
```

`06_rollback.sql` reads the previous version from `PROMOTION_LOG` and runs the
same two statements pointed backwards. Named versions are immutable, so a rollback
restores exactly the configuration that served before.

Before promoting, evaluate the candidate by version. The
[agent evaluations recipe](https://publish-p57963-e462098.adobeaemcloud.com/en/developers/guides/ai-cookbook/agent-evaluations/) runs the same
dataset against two committed versions and promotes the winner with this alias
move. Agent evaluations have four system metrics: answer correctness, logical
consistency, tool selection accuracy, and tool execution accuracy. The two tool
metrics are in Public Preview.

### Import a version from a stage

The Git-based path skips editing LIVE. CI puts the merged `agent_spec.yaml` in a
stage folder (or reads it from a Git repository stage) and imports it:

```sql
ALTER AGENT RELEASE_AGENT ADD VERSION FROM @AGENT_SPECS/release_v3
  COMMENT = 'v3: imported from stage';
```

The folder must contain `agent_spec.yaml`, the same layout Snowflake uses for each
version: `LIST 'snow://agent/<db>.<schema>.RELEASE_AGENT/versions/VERSION$1/'`
shows it. `ADD VERSION FROM` fails while a LIVE version exists, so an agent that
is deployed from CI should not keep one. `07` commits a leftover LIVE as a
snapshot first. The imported version counts as `LAST`.

## Verify

After `01` through `07`:

- `DESCRIBE AGENT COOKBOOK_AGENT_VERSIONING_AND_PROMOTION.AGENTS.RELEASE_AGENT`
  shows `default_version_name` = `VERSION$1` and an `aliases` map with
  `PRODUCTION` on `VERSION$1` and `CANARY` on the imported version.
- `SHOW VERSIONS IN AGENT ...` lists VERSION$1 (PRODUCTION, default), VERSION$2
  (the committed candidate), VERSION$3 (the LIVE snapshot committed by 07), and
  VERSION$4 (CANARY, "v3: imported from stage").
- `03` returns `[v1]` for PRODUCTION, DEFAULT, no suffix, and FIRST; `[v2]` for
  CANARY, LAST, and LIVE; and error 399535 for the lowercase alias.
- `AB_REQUEST_LOG` shows one bucket per routing key, `CANARY` rows with `[v2]`,
  and `PRODUCTION` rows with `[v1]`.
- `PROMOTION_LOG` has one `promote` row (VERSION$1 to VERSION$2) and one
  `rollback` row (VERSION$2 to VERSION$1).

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Error 399535 "Version 'production' not found" | Unquoted aliases are stored in uppercase and the suffix is matched as written | Call `!PRODUCTION`, or create the alias as a double-quoted identifier and call it with that exact case |
| Unversioned callers suddenly get the new version after a commit | DEFAULT follows the newest commit when it is not pinned | `SET DEFAULT_VERSION = 'VERSION$N'` and move it as part of promotion |
| `SET DEFAULT_VERSION = LAST` fails with "syntax error ... unexpected 'LAST'" | The unquoted keyword form is rejected. This differs from the published example on the [versioning page](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-versioning#default-version), which shows `SET DEFAULT_VERSION = LAST;` | Quote it: `SET DEFAULT_VERSION = 'LAST'`. `DESCRIBE AGENT` then shows `default_version_name` = `LAST`, and DEFAULT follows each new version. |
| CANARY disappears after promotion | A version holds at most one alias; setting PRODUCTION on the CANARY version replaces CANARY | Expected. Point CANARY at the next candidate when you have one, and stop CANARY routing until then. |
| Setting PRODUCTION on another version does not error | The alias moves: the new version gets it and the previous holder loses it. This differs from the Limitations list on the [versioning page](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-versioning#limitations), which says assigning an alias that exists on another version is an error; the same page's Aliases section describes the reassignment that this recipe relies on | Record the previous holder before moving it, as `05` does, so you can roll back |
| An alias set on LIVE ends up on a named version | Committing LIVE carries its alias to the new `VERSION$N` | Put aliases on named versions only, or expect the move |
| "There is already a live version. Please commit it first." | `ADD LIVE VERSION` or `ADD VERSION FROM @stage` while LIVE exists | Commit LIVE first; LIVE cannot be dropped |
| `MODIFY VERSION LAST SET ALIAS` is a syntax error | `MODIFY VERSION` takes a system name, not a shortcut | Resolve the shortcut through `DESCRIBE AGENT` (`aliases` column) first |
| `DATA_AGENT_RUN` compile error "needs to be constant" | The agent argument came from a column or expression | Choose between literal references, or set a session variable |

## Teardown

Run `sql/99_teardown.sql` as ACCOUNTADMIN. It drops the database (with the agent, every version,
the stage, and the log tables), the warehouse, and the role. Nothing at the
account level needs to be restored.

## Run it with a coding agent

```text
Install or enable the bundled agent-studio skill if it is not already available.
Then, in the recipe folder recipes/cortex-agents/agent-versioning-and-promotion:
1. Confirm the target account with SELECT CURRENT_ACCOUNT(), CURRENT_ROLE(),
   and show me the result before creating anything.
2. Run sql/01_setup.sql through sql/07_import_version_from_stage.sql in order,
   stopping on the first error.
3. After each file, run DESCRIBE AGENT
   COOKBOOK_AGENT_VERSIONING_AND_PROMOTION.AGENTS.RELEASE_AGENT and report
   default_version_name and the aliases map.
4. Compare the results with the Verify section of README.md.
5. Only touch objects whose names start with COOKBOOK_AGENT_VERSIONING.
   Run sql/99_teardown.sql when I say so; it uses ACCOUNTADMIN for the drops.
```

## Related skills

- `agent-studio` (bundled with Cortex Code): builds, evaluates, and optimizes
  Cortex Agents. Use it to create the evaluation dataset and runs that decide
  whether a candidate version is promoted.

## References

- [Cortex Agent versioning](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-versioning)
- [Create and manage agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [ALTER AGENT](https://docs.snowflake.com/en/sql-reference/sql/alter-agent)
- [Cortex Agents Run API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run)
- [Cortex Agent evaluations](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)
- [Caller's rights and owner's rights stored procedures](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-rights)
