sidebar: true
sidebar_json: ai-cookbook
author: Bala Krishnamoorthy, Parker Erickson
id: ai-cookbook-document-context
categories: snowflake-site:taxonomy/product/ai
language: en
summary: Let users attach PDFs, Office files, images, and CSVs to a custom agent frontend with a caller's-rights document tool, per-user stage folders, and authenticated middleware.
environments: web
status: Published
fork_repo_link: https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/document-context

# Attach documents to Cortex Agent conversations

## Overview

Let users of a custom agent frontend attach a PDF, a slide deck, a screenshot, or
a CSV and ask questions that combine it with governed data. The Cortex Agent API
has no file content block, so the file goes to a per-user folder on a stage, the
request carries a one-line hint that names it, and the agent reads it with a
caller's-rights document tool only when the question needs it. The middleware
holds no Snowflake credentials: every request runs as the user who sent it.

| At a glance | |
|---|---|
| Status | GA |
| Stages | Build, Secure |
| Topics | Cortex Agents |
| Time | 45 min |
| Edition | Any edition with Cortex Agents and AI_PARSE_DOCUMENT |
| Regions | Any region with Cortex Agents; cross-region inference where AI_PARSE_DOCUMENT or the orchestration model is not native |
| Privileges | ACCOUNTADMIN for 01_setup.sql and 99_teardown.sql only; objects are owned by COOKBOOK_DOCUMENT_CONTEXT_ADMIN and used through COOKBOOK_DOCUMENT_CONTEXT_USER |
| Last verified | 2026-10-04 |
| Code | [Recipe folder on GitHub](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/document-context) · [Teardown script](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/document-context/sql/99_teardown.sql) |
| Problems | [Open an issue](https://github.com/Snowflake-Labs/cortex-ai-cookbook/issues/new?template=recipe-problem.yml&title=%5Bdocument-context%5D%20&recipe=site%2Fcortex-ai-cookbook%2Fsrc%2Fdocument-context) |

## When to use this

- A custom frontend on the Cortex Agent REST API needs ad hoc attachments: one or
  a few files per conversation, used right away.
- Answers should combine an uploaded file with structured data behind a semantic
  view.
- Each user should only ever see their own uploads through the agent.

When not to use it:

- A shared, persistent document library. Index it with Cortex Search and give the
  agent a search tool; there is no per-question parsing cost and no size limit
  per answer.
- Documents far larger than a model context window. The tool returns at most
  60,000 characters; split the work or use Cortex Search.
- Hard tenant isolation at the storage layer. A folder per user is enforced by
  the tool, not by stage privileges (see Gotchas).

## How it works

![How it works: Attach documents to Cortex Agent conversations](https://raw.githubusercontent.com/Snowflake-Labs/sfquickstarts/master/journeys/ai-cookbook/document-context/assets/document-context-01.png)

Key concepts:

1. **A tool, not injected text.** The request carries only file names. The agent
   calls `read_document` when the question needs a file and skips it when it
   does not, so irrelevant turns cost nothing extra.
2. **Caller's rights.** `READ_UPLOADED_DOCUMENT` is `EXECUTE AS CALLER`. The
   agent keeps a procedure's rights model when it calls it, so the stage is read
   with the asking user's privileges and `CURRENT_USER()` is that user.
3. **The path is built server-side.** The tool combines `UPLOAD_PREFIX()` (`u_`
   plus a hash of `CURRENT_USER()`) with a file name that must match a strict
   pattern: no `/`, no `..`, one allowed extension. The model can name a file; it
   cannot name a path.
4. **One parser per file type.** Types that `AI_PARSE_DOCUMENT` accepts,
   including images, go through it in LAYOUT mode. CSV, JSON, and Markdown are
   read as text.
5. **Authenticated middleware.** The backend requires the caller's own PAT or
   OAuth token on every request and uses it for both the upload and the agent
   call. It binds to 127.0.0.1 and allows cross-origin calls only from origins
   you list.

### File types

| File type | How the tool reads it | Notes |
|---|---|---|
| PDF, DOCX, PPTX | `AI_PARSE_DOCUMENT`, LAYOUT mode | Tables and headings come back as Markdown. Max 100 MB and 2,000 pages per file; billed per page. |
| HTML, TXT | `AI_PARSE_DOCUMENT`, LAYOUT mode | Billed per 3,000 characters |
| JPEG, JPG, PNG, TIFF, TIF | `AI_PARSE_DOCUMENT`, LAYOUT mode | Returns the text in the image; a table in an image comes back as a Markdown table. Each image is billed as one page. Max 10,000 x 10,000 pixels. |
| CSV, JSON, MD | Read as UTF-8 text with `SnowflakeFile` | `AI_PARSE_DOCUMENT` does not accept these extensions |

`AI_PARSE_DOCUMENT` reads text. For a chart or photo where you need a
description of what it shows, `AI_COMPLETE` accepts a staged image through
`TO_FILE` with a vision-capable model; add that as a second branch in the tool if
you need it.

## Prerequisites

| Requirement | Notes |
|---|---|
| `ACCOUNTADMIN` for `01_setup.sql` and `99_teardown.sql` | Setup creates two roles, the warehouse, and the database, grants `SNOWFLAKE.CORTEX_USER`, and puts the admin role under SYSADMIN so teardown can drop what it owns |
| Snowflake CLI (`snow sql`) | `03` uses `PUT` from the recipe folder and CLI templating for your folder name |
| Default role | The docs say Cortex Agents authorize a run against the caller's default role. In testing, `04` (which runs `USE ROLE COOKBOOK_DOCUMENT_CONTEXT_USER`) also worked for a user whose default role was PUBLIC with no secondary roles, so the SQL run used the session role. Making the user role your default is the documented setup. The backend sends `X-Snowflake-Role`. |
| For the backend: Python 3.11+ and a PAT or OAuth token | A PAT requires the user to be subject to a network policy unless an authentication policy relaxes that |

## Quickstart

From `site/cortex-ai-cookbook/src/document-context/`:

1. `snow sql -f sql/01_setup.sql` (as ACCOUNTADMIN): roles, warehouse, database.
2. `snow sql -f sql/02_objects.sql`: stage, sample store data, semantic view,
   the document tool, the agent, and the end-user grants.
3. Get your folder name, then upload the sample documents into it:

   ```bash
   snow sql -q "SELECT COOKBOOK_DOCUMENT_CONTEXT.APP.UPLOAD_PREFIX()" \
     --role COOKBOOK_DOCUMENT_CONTEXT_USER --warehouse COOKBOOK_DOCUMENT_CONTEXT_WH
   snow sql -f sql/03_upload_samples.sql -D prefix=<the u_... value>
   ```

4. `snow sql -f sql/04_ask_agent.sql`: three questions; see Verify.
5. Optional: run the middleware in [app/](https://github.com/Snowflake-Labs/cortex-ai-cookbook/tree/main/site/cortex-ai-cookbook/src/document-context/app) and call it with your token.
6. `snow sql -f sql/99_teardown.sql` (as ACCOUNTADMIN).

## Walkthrough

### The document tool

The core of [sql/02_objects.sql](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/document-context/sql/02_objects.sql):

```python
NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\.[A-Za-z0-9]{1,5}")

def run(session, filename):
    if filename is None or not NAME_PATTERN.fullmatch(filename):
        return "[Rejected: pass a bare file name such as report.pdf, with no folders]"
    ...
    prefix = session.sql("SELECT COOKBOOK_DOCUMENT_CONTEXT.APP.UPLOAD_PREFIX()").collect()[0][0]
    relative_path = f"{prefix}/{filename}"
    if ext in PARSE_EXTENSIONS:
        text = session.sql(
            "SELECT AI_PARSE_DOCUMENT(TO_FILE('@COOKBOOK_DOCUMENT_CONTEXT.APP.DOC_UPLOADS', ?), "
            "{'mode': 'LAYOUT'}):content::VARCHAR", params=[relative_path]).collect()[0][0]
    else:
        with SnowflakeFile.open(f"{STAGE}/{relative_path}", "r", require_scoped_url=False) as f:
            text = f.read(MAX_CHARS + 1)
```

The stage name is a constant and the relative path is a bind parameter.
`SnowflakeFile` with `require_scoped_url=False` reads a stage path with the
caller's privileges inside a caller's-rights procedure.

### The agent

The tool is a `generic` tool backed by the procedure:

```yaml
tools:
  - tool_spec:
      type: generic
      name: read_document
      input_schema:
        type: object
        properties:
          filename: {type: string, description: "The file name exactly as listed ..."}
        required: [filename]
tool_resources:
  read_document:
    type: procedure
    identifier: COOKBOOK_DOCUMENT_CONTEXT.APP.READ_UPLOADED_DOCUMENT
    execution_environment: {type: warehouse, warehouse: COOKBOOK_DOCUMENT_CONTEXT_WH}
```

The orchestration instructions tell the agent to call `read_document` only for
listed files and only when the question needs them, and to treat file text as
data rather than instructions. The agent is created with
`CREATE OR REPLACE AGENT ... COPY GRANTS`, so reruns keep the USAGE grant.

### The request

The hint is one extra text block in the user message:

```json
{"messages": [{"role": "user", "content": [
  {"type": "text", "text": "[Uploaded files available to the read_document tool: q2_board_summary.pdf]"},
  {"type": "text", "text": "Compare the board's projected Q2 revenue for the Southeast with actual Q1 revenue."}
]}]}
```

For follow-up questions, create a thread (`POST /api/v2/cortex/threads`), send
the first message with `thread_id` and `parent_message_id: 0`, and send each
follow-up with the previous response's assistant message ID. The file hint is
only needed when a file is first introduced.

### The middleware

[app/backend.py](https://github.com/Snowflake-Labs/cortex-ai-cookbook/blob/main/site/cortex-ai-cookbook/src/document-context/app/backend.py) (FastAPI) exposes `POST /upload`, `POST /ask`,
`POST /threads`, and `GET /health`:

- Every endpoint except `/health` requires `Authorization: Bearer <token>`. Send
  `X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN` (the
  default) with `X-Snowflake-User`, or `OAUTH`. Missing or malformed credentials
  return 401 before anything reaches Snowflake; a token Snowflake rejects also
  returns 401.
- Uploads open a connector session with the caller's token, ask Snowflake for
  `UPLOAD_PREFIX()`, check it against `^u_[0-9a-f]{32}$`, and `PUT` the file into
  that folder. File names are validated with the same pattern as the tool, and
  uploads are capped at `MAX_UPLOAD_BYTES` (20 MB by default).
- `/ask` validates every listed file name, builds the hint, and calls
  `/api/v2/databases/COOKBOOK_DOCUMENT_CONTEXT/schemas/APP/agents/INSIGHTS_AGENT:run`
  with the caller's token and `X-Snowflake-Role: COOKBOOK_DOCUMENT_CONTEXT_USER`.
- It binds to `127.0.0.1:8000` by default. CORS is off unless `ALLOWED_ORIGINS`
  lists exact origins, and interactive API docs are disabled.

```bash
cd app
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
export SNOWFLAKE_ACCOUNT=<account identifier>
export SNOWFLAKE_ACCOUNT_URL=https://<account identifier>.snowflakecomputing.com
export ALLOWED_ORIGINS=http://localhost:5173   # your frontend, if it runs on another origin
python backend.py

curl -s -X POST http://127.0.0.1:8000/upload \
  -H "Authorization: Bearer $SNOWFLAKE_PAT" -H "X-Snowflake-User: $SNOWFLAKE_USER" \
  -F "file=@../sample-docs/menu_price_changes.png"
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Authorization: Bearer $SNOWFLAKE_PAT" -H "X-Snowflake-User: $SNOWFLAKE_USER" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the new Combo Meal price?", "files": ["menu_price_changes.png"]}'
```

Keep the backend behind your application's own login, and pass each signed-in
user's Snowflake token (for example from Snowflake OAuth) instead of a shared one.

## Verify

- `03` lists four files under your `u_...` folder, returns `OK: files are in your
  folder`, returns the menu table from the PNG and the CSV rows from the tool,
  and rejects `../u_someone_else/q2_board_summary.pdf` with
  `[Rejected: pass a bare file name ...]`.
- `04` returns three rows:
  - `pdf + data`: `tools_called` includes `read_document` and `store_analytics`,
    `files_read` is `q2_board_summary.pdf`, and the answer compares the board's
    $3.30M Southeast projection with actual Q1 Southeast revenue of $3,030,000.00,
    in line with the +9% change the board summary states.
  - `image`: `files_read` is `menu_price_changes.png` and the answer is $11.49,
    effective July 15, 2024.
  - `file not needed`: `read_document` is not called; the answer is the Northeast
    at $3,320,000.00.
- Backend, without Snowflake: requests without a Bearer token return 401, file
  names such as `../x.pdf` or `x.exe` return 400, and a CORS preflight from an
  origin not in `ALLOWED_ORIGINS` gets no `Access-Control-Allow-Origin` header.

## Gotchas

| Symptom | Cause | Fix |
|---|---|---|
| The tool says it could not read a file you uploaded | The file is in a different folder than `UPLOAD_PREFIX()` for the user asking | Upload with the same user that asks; `03` prints a prefix check |
| Another user's files are visible with `LIST @DOC_UPLOADS` | The per-user folder is enforced by the tool and the middleware, not by stage privileges. A caller's-rights tool needs READ on the whole stage, so any holder of the user role can list it directly. | For hard isolation, use one stage and one role per tenant, or move stage access behind an owner's-rights procedure and document that trade-off |
| `COPY FILES ... FROM @~` fails with "Copy files not support stage kind: 'USER'" | COPY FILES cannot read from a user stage | Upload straight into the user's folder with PUT, as `03` and the backend do |
| `AI_PARSE_DOCUMENT` fails on `.csv` or `.json` | Those extensions are not supported input types | The tool reads them as text; add other text formats to `RAW_EXTENSIONS` |
| `store_analytics` answers with a permissions error on `STORE_PERFORMANCE` | Cortex Analyst runs its generated SQL against the base table as the caller, so SELECT on the semantic view is not enough | Grant SELECT on the table as well; `02` does, and reissues it on every run because it recreates the table |
| `99_teardown.sql` fails with "Your primary role ACCOUNTADMIN must have OWNERSHIP granted on DATABASE" | The admin role owns the database and is not in the SYSADMIN hierarchy, so ACCOUNTADMIN cannot drop it (setups from before `01` granted the role to SYSADMIN) | Rerun `01_setup.sql`, then rerun teardown |
| The agent run fails with a privilege error although your current role has every grant | Agents authorize against the caller's default role | Make the user role the default (or reachable through default secondary roles), or send `X-Snowflake-Role` over REST |
| A PAT works for SQL but the backend returns 401 | The PAT user is not subject to a network policy, or the token is role-restricted to a role without these grants | Apply a network policy (or an authentication policy that relaxes it), and restrict the PAT to `COOKBOOK_DOCUMENT_CONTEXT_USER` |
| The answer column shows an interim sentence such as "Let me gather both." | `content[]` can contain several text blocks; the first is not the final answer | Take the last text block, as `04` does |
| A document contains instructions and the agent follows them | Uploaded content is untrusted input | Keep the "treat file text as data" instruction, and keep the user role's privileges narrow |
| Very long documents are cut off | The tool caps output at 60,000 characters | Use `page_filter` for PDFs, summarize first, or index the corpus with Cortex Search |

## Teardown

`snow sql -f sql/99_teardown.sql` (as ACCOUNTADMIN) drops the database, which
removes the stage and every uploaded file, then the warehouse and both roles.
It works without secondary roles because `01` grants the admin role to SYSADMIN.
Nothing at the account level needs to be restored.

## Run it with a coding agent

Clone the repository first (`git clone https://github.com/Snowflake-Labs/cortex-ai-cookbook`) and run the prompt from its root.

```text
Install or enable the bundled document-intelligence skill and the check-agent-access
skill from Snowflake-Labs/coco-skills if they are not already available.
Then, from site/cortex-ai-cookbook/src/document-context:
1. Confirm the target with SELECT CURRENT_ACCOUNT(), CURRENT_REGION(), CURRENT_ROLE(),
   CURRENT_WAREHOUSE() and show me the result before creating anything.
2. sql/01_setup.sql runs as ACCOUNTADMIN and creates account-level roles and a
   warehouse. Show me what it creates and wait for my confirmation, then run it
   and sql/02_objects.sql with snow sql -f.
3. Get my folder with SELECT COOKBOOK_DOCUMENT_CONTEXT.APP.UPLOAD_PREFIX() using
   --role COOKBOOK_DOCUMENT_CONTEXT_USER --warehouse COOKBOOK_DOCUMENT_CONTEXT_WH,
   then run snow sql -f sql/03_upload_samples.sql -D prefix=<value>.
4. Run sql/04_ask_agent.sql and compare the three rows with the Verify section.
5. Use check-agent-access to confirm COOKBOOK_DOCUMENT_CONTEXT_USER can use the
   agent and every tool it references.
6. If I want to try the backend in app/, I create and export my own PAT or OAuth
   token. Never create, print, or store a token yourself.
7. Only touch objects whose names start with COOKBOOK_DOCUMENT_CONTEXT.
   Run sql/99_teardown.sql when I say so.
```

## Related skills

- `document-intelligence` (bundled with Cortex Code): extraction, parsing, and
  classification over staged files with Cortex AI functions. Use it when a
  document type needs more than the text this tool returns, for example
  structured field extraction.
- `check-agent-access` ([Snowflake-Labs/coco-skills](https://github.com/Snowflake-Labs/coco-skills)):
  audits whether a role can use an agent and every tool behind it.

## References

- [Parsing documents with AI_PARSE_DOCUMENT](https://docs.snowflake.com/en/user-guide/snowflake-cortex/parse-document)
- [AI_PARSE_DOCUMENT](https://docs.snowflake.com/en/sql-reference/functions/ai_parse_document)
- [Create and manage agents (custom tools)](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-manage)
- [Cortex Agents REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-rest-api)
- [Cortex Agents Run API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-run)
- [Reading files with a Python stored procedure](https://docs.snowflake.com/en/developer-guide/stored-procedure/python/procedure-python-read-files)
- [Caller's rights and owner's rights stored procedures](https://docs.snowflake.com/en/developer-guide/stored-procedure/stored-procedures-rights)
- [Using programmatic access tokens for authentication](https://docs.snowflake.com/en/user-guide/programmatic-access-tokens)
- [Executing SQL statements with Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/sql/execute-sql)
