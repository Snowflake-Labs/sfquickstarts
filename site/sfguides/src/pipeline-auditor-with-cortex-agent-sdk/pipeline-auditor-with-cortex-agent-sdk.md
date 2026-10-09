author: Dash Desai, James Cha-Earley
id: pipeline-auditor-with-cortex-agent-sdk
language: en
summary: Build an AI-powered pipeline auditor that discovers and analyzes your Snowflake data pipelines using the Cortex Agent SDK and Snowflake App Runtime.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/ai
environments: web
status: Published
feedback link: https://github.com/Snowflake-Labs/sfguides/issues
tags: Cortex, Agent, SDK, TypeScript, AI, App Runtime, Next.js
fork repo link: https://github.com/sfc-gh-JCHAEARLEY/sfguide-pipeline-auditor-with-cortex-agent-sdk

# Building a Pipeline Auditor with the Cortex Agent SDK

<!-- ------------------------ -->
## Overview
Duration: 5

Data pipelines break silently. A task suspends, a dynamic table stops refreshing, a stream goes stale -- and nobody notices until a dashboard goes blank or a downstream consumer raises an alarm. Manual health checks don't scale, and static monitors only catch what you thought to look for.

In this guide you will build a **Pipeline Auditor** -- a full-stack application that uses a Cortex AI coding agent to automatically discover every object in a Snowflake database (or a single schema), run health checks against each one, and produce a structured JSON report with severity-rated findings. When something looks wrong, the agent can suggest a fix and even execute it for you.

The app runs on **Snowflake App Runtime** (SAR) as a Next.js application and uses the **@snowflake/cortex-agent-sdk** TypeScript SDK to communicate with the coding agent.

### What You'll Need
- A Snowflake account with Cortex AI enabled (Enterprise edition or higher)
- Node.js 22+ and npm
- Snowflake CLI (`snow`) installed and configured
- Basic TypeScript and React knowledge

### What You'll Learn
- How to scaffold and deploy a Next.js app on Snowflake App Runtime
- How to use `@snowflake/cortex-agent-sdk` to run coding agent sessions
- How to build composable system prompts that produce structured JSON output
- How to create a poll-based streaming architecture for real-time progress
- How to implement AI-powered fix suggestions with multi-turn chat

### What You'll Build
- A full-stack pipeline auditor with:
  - Database and schema discovery
  - Configurable audit scope (tables, dynamic tables, tasks, views, streams, pipes, procedures)
  - Real-time audit progress tracking via a sidebar
  - Structured health reports with severity ratings (critical / warning / info)
  - AI-powered "Suggest Fix" with follow-up chat and SQL execution

<!-- ------------------------ -->
## Setup
Duration: 10

### Create Snowflake Objects

Run the following SQL in Snowsight to create the database the app will audit. You can also point the auditor at any existing database -- this one is just a convenient starting point.

```sql
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS PIPELINE_AUDITOR_DB;
CREATE SCHEMA IF NOT EXISTS PIPELINE_AUDITOR_DB.AUDITOR;
```

### Scaffold the App

Clone the companion repository and navigate to the project:

```bash
git clone https://github.com/sfc-gh-JCHAEARLEY/sfguide-pipeline-auditor-with-cortex-agent-sdk.git
cd sfguide-pipeline-auditor-with-cortex-agent-sdk
```

Install dependencies:

```bash
npm install
```

### Project Structure

The project follows a standard Next.js App Router layout:

```
pipeline-auditor/
  app/
    api/
      audit/          # POST to start audit, GET to poll progress
      suggest-fix/    # POST to request fix, chat/ for follow-up, dismiss/
      databases/      # GET available databases
      schemas/        # GET schemas in a database
      chat/           # POST for follow-up chat on the audit thread
    page.tsx          # Root page -- providers + AuditDashboard
  components/
    AuditDashboard.tsx   # Main layout orchestrator
    AuditHeader.tsx      # Database/schema dropdowns + scope picker
    AuditSidebar.tsx     # Real-time tool call progress
    ChatThread.tsx       # Message thread with inline report accordion
    EmptyState.tsx       # Landing page
  hooks/
    useAudit.ts          # Poll-based audit state machine
    useSuggestFix.ts     # Fix request + multi-turn follow-up
  lib/
    agent-client.ts      # CortexAgentClient factory
    audit-engine.ts      # Composable system prompt + JSON schema
    audit-store.ts       # In-memory job store for poll-based streaming
    types.ts             # Shared TypeScript types
  app.yml                # SAR build/run manifest
```

### Environment Variables (Local Dev Only)

When running locally with `npm run dev`, create a `.env.local` file:

```
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_PAT=your_personal_access_token
```

When deployed to SAR, the app reads an OAuth token from the SPCS runtime automatically -- no env vars needed.

<!-- ------------------------ -->
## Build the Audit Engine
Duration: 15

The audit engine is the core of the application. It creates a Cortex AI coding agent session, feeds it a composable system prompt, and streams back structured results. Four files work together to make this happen.

### Agent Client Factory

`lib/agent-client.ts` creates a `CortexAgentClient` instance that works in both environments:

```typescript
import { CortexAgentClient, OAuthAuth } from "@snowflake/cortex-agent-sdk";
import fs from "fs";

const TOKEN_PATH = "/snowflake/session/token";

export function createAgentClient(): CortexAgentClient {
  const account = process.env.SNOWFLAKE_ACCOUNT || "";

  // In SAR (SPCS), the runtime mounts an OAuth token at a known path
  if (fs.existsSync(TOKEN_PATH)) {
    const token = fs.readFileSync(TOKEN_PATH, "utf-8").trim();
    return new CortexAgentClient({
      account,
      auth: new OAuthAuth(token),
    });
  }

  // Fall back to PAT for local development
  const pat = process.env.SNOWFLAKE_PAT || "";
  return new CortexAgentClient({ account, auth: pat });
}
```

The dual-auth pattern is important: SAR containers get a short-lived OAuth token injected at `/snowflake/session/token` by the SPCS runtime. For local development, you use a Personal Access Token (PAT) instead.

### Composable System Prompt

`lib/audit-engine.ts` is where the real intelligence lives. Rather than one monolithic prompt, the audit instructions are split into composable sections keyed by scope:

```typescript
export const PROMPT_SECTIONS: Record<string, string> = {
  tables_freshness: `
TABLES & FRESHNESS:
   - Tables and row counts:
     SELECT table_schema, table_name, table_type, row_count
     FROM <DATABASE>.INFORMATION_SCHEMA.TABLES
     WHERE table_schema NOT IN ('INFORMATION_SCHEMA')
     ORDER BY table_schema, table_name;
   - Check freshness -- identify stale tables:
     SELECT table_schema, table_name, table_type, row_count, last_altered,
            DATEDIFF('hour', last_altered, CURRENT_TIMESTAMP()) AS hours_since_update,
            CASE
              WHEN DATEDIFF('hour', last_altered, CURRENT_TIMESTAMP()) > 168 THEN 'critical'
              WHEN DATEDIFF('hour', last_altered, CURRENT_TIMESTAMP()) > 24 THEN 'warning'
              ELSE 'fresh'
            END AS freshness_status
     FROM <DATABASE>.INFORMATION_SCHEMA.TABLES
     WHERE table_schema NOT IN ('INFORMATION_SCHEMA') AND table_type = 'BASE TABLE'
     ORDER BY hours_since_update DESC;
   - Check for row count anomalies (empty tables that shouldn't be)`,

  dynamic_tables: `
DYNAMIC TABLES:
   - Discover: SHOW DYNAMIC TABLES IN DATABASE <DATABASE>;
   - Check scheduling_state (should be ACTIVE)
   - Check refresh history for failures ...`,

  tasks: `
TASKS:
   - Discover: SHOW TASKS IN DATABASE <DATABASE>;
   - Check execution history for failures via TASK_HISTORY table function
   - Flag suspended tasks and tasks with recent failures`,

  streams: `
STREAMS:
   - Discover: SHOW STREAMS IN DATABASE <DATABASE>;
   - Check each stream's stale status (stale = true is CRITICAL)
   - Check stale_after timestamp -- if approaching, flag as warning`,

  pipes: `
PIPES:
   - Discover: SHOW PIPES IN DATABASE <DATABASE>;
   - Check pipe status (RUNNING, STOPPED_CLONING, PAUSED, STALLED)
   - Check recent copy history for errors ...`,

  procedures: `
STORED PROCEDURES:
   - Discover: SHOW PROCEDURES IN DATABASE <DATABASE>;
   - Identify ETL-related procedures
   - Flag procedures that do data movement but have no associated task`,
};
```

The `buildSystemPrompt` function assembles only the sections the user selected:

```typescript
export function buildSystemPrompt(
  database: string,
  scope: string[],
  schema: string,
): string {
  const allScopes = Object.keys(PROMPT_SECTIONS);
  const activeScopes = scope.length > 0 ? scope : allScopes;

  // Use the single-schema preamble when a schema is specified
  let prompt = schema
    ? PROMPT_PREAMBLE_SINGLE_SCHEMA
    : PROMPT_PREAMBLE_ALL_SCHEMAS;

  for (const key of allScopes) {
    if (activeScopes.includes(key)) {
      prompt += PROMPT_SECTIONS[key];
    }
  }
  prompt += PROMPT_FOOTER;

  // Replace <DATABASE> and <SCHEMA> placeholders throughout
  prompt = prompt.replace(/<DATABASE>/g, database);
  if (schema) {
    prompt = prompt.replace(/<SCHEMA>/g, schema);
    // Rewrite SHOW ... IN DATABASE to SHOW ... IN SCHEMA
    // Rewrite INFORMATION_SCHEMA filters to target the single schema
  }

  return prompt;
}
```

This composability matters: auditing only tasks and streams is much faster than auditing everything. The user picks the scope in the UI, and the prompt adapts.

The engine also defines `AUDIT_REPORT_SCHEMA` -- a JSON schema that tells the agent exactly what structure to return. The schema includes a `pipeline_inventory` (what was discovered), a `findings` array (each with `category`, `severity`, `object`, and `message`), and a `summary` with counts and an `overall_health` rating.

### In-Memory Job Store

Because the audit can take 30-60 seconds, the app uses a poll-based architecture instead of holding an HTTP connection open. `lib/audit-store.ts` is the glue:

```typescript
export interface AuditJob {
  events: Record<string, unknown>[];
  done: boolean;
  error?: string;
}

export const jobStore = new Map<string, AuditJob>();

export function pushJobEvent(
  jobId: string,
  event: Record<string, unknown>,
): void {
  const job = jobStore.get(jobId);
  if (job) job.events.push(event);
}
```

Events accumulate in memory. The frontend polls for new events every 2 seconds. A cleanup interval removes completed jobs after 30 minutes.

### The Audit API Route

`app/api/audit/route.ts` ties everything together. The POST handler:

1. Accepts `database`, `scope`, and `schema` from the request body
2. Creates a job ID and registers it in the job store
3. Returns the job ID immediately (non-blocking)
4. Fires `runAuditJob` in the background

The background function:

```typescript
async function runAuditJob(jobId, database, scope, schema) {
  const client = createAgentClient();
  const systemPrompt = buildSystemPrompt(database, scope, schema);
  const userPrompt = buildAuditUserPrompt(database, scope, schema);

  const messages = [
    {
      role: "user",
      content: [{ type: "text", text: systemPrompt + "\n\n" + userPrompt }],
    },
  ];

  const stream = client.codingAgent.stream({
    permissionPolicy: "always_allow",
    messages,
  });

  let accumulatedText = "";

  // Use the SDK's callback API to process events
  stream.on("text", (delta, accumulated) => {
    accumulatedText = accumulated;
    // Try to parse as JSON report on each chunk
    try {
      const parsed = JSON.parse(accumulated);
      if (parsed.findings) {
        pushJobEvent(jobId, { type: "report", report: parsed });
      }
    } catch { /* not complete JSON yet */ }
  });

  stream.on("toolUse", (ev) => {
    // Push progress events so the sidebar shows tool execution
    pushJobEvent(jobId, { type: "tool_progress", toolName: ev.name });
  });

  stream.on("thinking", (delta) => {
    pushJobEvent(jobId, { type: "thinking", text: delta });
  });

  await stream.done();
  // Job is complete — mark done in the job store
}
```

The stream uses the SDK's callback API to process three event types:

- **text** -- accumulated until it forms valid JSON matching the report schema
- **toolUse** -- emitted as progress events so the sidebar can show what the agent is doing
- **thinking** -- the agent's chain-of-thought reasoning

> **Key concepts:**
> - **Coding agent sessions** give the AI access to `sql_execute` so it can query your Snowflake account directly
> - **Composable prompts** let you scope audits to specific object types for faster, targeted checks
> - **Poll-based streaming** avoids long-lived HTTP connections while still giving the user real-time progress
> - **Structured JSON output** means the report is machine-parseable, not just freeform text

<!-- ------------------------ -->
## Build the Dashboard UI
Duration: 10

The frontend is a single-page React application built with Material UI. The component hierarchy is straightforward.

### Page Root and Providers

`app/page.tsx` wraps the dashboard in the required providers:

```typescript
"use client";

import { AppThemeProvider } from "@/components/ThemeContext";
import { AuditDashboard } from "@/components/AuditDashboard";

export default function Page() {
  return (
    <AppThemeProvider>
      <AuditDashboard />
    </AppThemeProvider>
  );
}
```

`AppThemeProvider` wraps the app in the MUI dark/light theme with localStorage persistence.

### AuditDashboard -- The Orchestrator

`AuditDashboard.tsx` connects the hooks to the layout:

```typescript
export function AuditDashboard() {
  const {
    isAuditing, isLoading, report, messages,
    toolProgress, error, stats,
    startAudit, cancelAudit, resetView,
  } = useAudit();

  const { fixState, requestFix, sendFollowUp, dismissFix } = useSuggestFix();

  return (
    <Box sx={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <AuditHeader
        onStartAudit={(db, scope, schema) => startAudit(db, scope, schema)}
        onCancel={cancelAudit}
        onReset={resetView}
        isLoading={isLoading}
        isAuditing={isAuditing}
      />

      <Box sx={{ flex: 1, overflow: "hidden", display: "flex" }}>
        {!hasAuditData ? (
          <EmptyState />
        ) : (
          <>
            {/* Chat thread with inline report accordion */}
            <Box sx={{ flex: 1, overflow: "auto" }}>
              <ChatThread
                messages={messages}
                report={report}
                toolProgress={toolProgress}
                isLoading={isLoading}
                onSuggestFix={handleSuggestFix}
                fixState={fixState}
              />
            </Box>

            {/* Real-time stats sidebar */}
            <AuditSidebar
              toolProgress={toolProgress}
              report={report}
              stats={stats}
              isLoading={isLoading}
            />
          </>
        )}
      </Box>
    </Box>
  );
}
```

The layout has three zones:
- **AuditHeader** -- database and schema selectors (fetched via `/api/databases` and `/api/schemas`), scope checkboxes, and the "Run Audit" button
- **ChatThread** -- the main content area showing the conversation, tool call activity, and the audit report as an expandable accordion with severity badges
- **AuditSidebar** -- a live feed of tool calls with SQL previews and elapsed time

### The useAudit Hook -- Poll-Based State Machine

The `useAudit` hook drives the audit lifecycle. The core polling function is reused by both audit and fix flows:

```typescript
const POLL_INTERVAL_MS = 2000;

export async function pollJob(
  jobId: string,
  onEvent: (event: StreamEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  let cursor = 0;
  while (!signal.aborted) {
    const resp = await fetch(
      `/api/audit/progress?jobId=${encodeURIComponent(jobId)}&after=${cursor}`,
      { credentials: "include", signal },
    );
    const data = await resp.json();
    for (const event of data.events) {
      onEvent(event);
    }
    cursor = data.cursor;
    if (data.done) return;
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
}
```

The `startAudit` callback POSTs to `/api/audit`, gets back a `jobId`, then polls for events. Each event type maps to a state update:

| Event type | State change |
|---|---|
| `tool_progress` | Appends to sidebar + message tool call list |
| `thinking` | Appends to the assistant message's thinking steps |
| `report` | Sets the parsed audit report |
| `result` | Clears loading state, sets duration/tool call stats |
| `error` | Sets error message, clears loading |

The poll includes retry logic with exponential backoff for transient 5xx errors -- important since SAR proxies can occasionally hiccup.

> **Key concepts:**
> - **Cursor-based polling** ensures no events are missed even if a poll is delayed
> - **AbortController** lets the user cancel a running audit cleanly
> - **useEffect + fetch** handles the database/schema dropdowns with loading states

<!-- ------------------------ -->
## Add Suggest Fix
Duration: 10

After the audit produces findings, each one gets a "Suggest Fix" button. This opens a separate coding agent session focused on remediation.

### The Suggest Fix API

`app/api/suggest-fix/route.ts` creates a new agent session with a remediation-focused prompt:

```typescript
async function runSuggestFixJob(jobId, finding, database) {
  const systemPrompt = `You are a Snowflake pipeline remediation expert. 
When given a finding, respond with a clear, actionable fix. 
Use SQL code blocks for any commands. 
If the user asks you to run SQL, you may use sql_execute.
Target database: ${database}.`;

  const userPrompt = `Suggest a concrete fix for this pipeline audit finding:

Finding:
- Severity: ${finding.severity}
- Category: ${finding.category}
- Object: ${finding.object}
- Message: ${finding.message}
${finding.details ? `- Details: ${JSON.stringify(finding.details)}` : ""}

Rules:
- Do NOT run any tools or queries. Respond with your answer directly.
- Provide exact SQL commands in fenced code blocks.
- Explain briefly why the fix works.
- Keep the response under 500 words.`;

  const messages = [{
    role: "user",
    content: [{ type: "text", text: systemPrompt + "\n\n" + userPrompt }],
  }];

  const client = createAgentClient();
  const stream = client.codingAgent.stream({
    permissionPolicy: "always_allow",
    messages,
  });

  // Use callbacks to stream text to the job store
  stream.on("text", (delta) => {
    pushJobEvent(jobId, { type: "text", text: delta });
  });

  await stream.done();

  // Save the conversation thread for follow-up chat
  setFixSession([...messages, {
    role: "assistant",
    content: [{ type: "text", text: stream.currentText }],
  }]);
}
```

The fix session is stored per-job in the job store so follow-up chat can continue the conversation without leaking state between requests.

### Multi-Turn Follow-Up Chat

The user can ask follow-up questions ("Can you also add a monitoring task?", "What about the downstream views?"). `app/api/suggest-fix/chat/route.ts` appends the new message to the stored thread and streams back the response:

```typescript
async function runFixChatJob(jobId: string, message: string) {
  const fixThread = getFixSession();
  const client = createAgentClient();

  // Append user message to the thread
  fixThread.push({
    role: "user",
    content: [{ type: "text", text: message }],
  });

  // Stream with full conversation history for context
  const stream = client.codingAgent.stream({
    permissionPolicy: "always_allow",
    messages: fixThread,
  });

  // ... accumulate text, push events, update thread
}
```

This is a true multi-turn conversation -- the agent sees every prior message, so it can refine its suggestions based on the user's feedback.

### The useSuggestFix Hook

On the frontend, `hooks/useSuggestFix.ts` manages the fix lifecycle:

```typescript
export function useSuggestFix() {
  const [state, setState] = useState<SuggestFixState>(IDLE);

  const requestFix = useCallback(async (index, finding, database) => {
    // POST to /api/suggest-fix, poll for text events
    // Update state with streaming assistant messages
  }, []);

  const sendFollowUp = useCallback(async (message) => {
    // POST to /api/suggest-fix/chat, poll for response
    // Append user message + streaming assistant response
  }, []);

  const dismissFix = useCallback(() => {
    // Abort, reset state, POST to /api/suggest-fix/dismiss
  }, []);

  return { fixState: state, requestFix, sendFollowUp, dismissFix };
}
```

The fix panel renders inline in the ChatThread component. Each finding in the report has a "Suggest Fix" button. When clicked, it opens a chat-like panel below the finding with the AI's suggestion and a text input for follow-ups.

### Copy and Run

SQL code blocks in fix suggestions include a **Copy** button so users can paste them into a Snowflake worksheet for execution.

> **Key concepts:**
> - **Separate agent sessions** for audit vs. fix keep concerns isolated and prompts focused
> - **Multi-turn chat** with full message history gives the agent context for iterative refinement
> - **Per-job thread state** (stored in the job store) keeps conversations isolated between requests
> - The coding agent uses `permissionPolicy: "always_allow"` because it needs to run SQL queries autonomously. Deploy the app with a **read-only role** to limit what the agent can do.

<!-- ------------------------ -->
## Deploy and Run
Duration: 10

### Generate the Deployment Manifest

The project includes an `app.yml` that defines the build and run phases:

```yaml
install:
  commands:
    - ["npm", "ci", "--include=dev"]

build:
  commands:
    - ["npm", "run", "build"]
    - ["cp", "-r", ".next/static", ".next/standalone/.next/static"]
    - ["cp", "-r", "public", ".next/standalone/public"]
    - ["rm", "-rf", "node_modules"]

run:
  command: ["node", ".next/standalone/server.js"]
```

The build uses Next.js standalone output mode, which bundles only the required Node.js modules into `.next/standalone/` for a smaller container image.

### Set Up and Deploy

From the project directory, run:

```bash
snow app setup
```

This generates a `snowflake.yml` with your deployment target (account, database, warehouse). Review it, then deploy:

```bash
snow app deploy
```

The deploy process:
1. Builds the Next.js app inside an SPCS container
2. Pushes the container image to the Snowflake image registry
3. Creates an APPLICATION SERVICE object
4. Makes the app available at a URL

### Open the App

After deployment completes, `snow app deploy` prints the app URL. Open it in your browser.

You can also find the URL with:

```bash
snow app status
```

### Run Your First Audit

1. **Select a database** from the dropdown in the header. The app queries `SHOW DATABASES` to populate the list.

2. **(Optional) Select a schema** to narrow the audit to a single schema instead of the entire database.

3. **Choose your audit scope** using the checkboxes. You can audit any combination of:
   - Tables and freshness
   - Dynamic tables
   - Tasks
   - Views
   - Streams
   - Pipes
   - Stored procedures

4. **Click "Run Audit"**. The sidebar lights up with real-time progress as the agent executes discovery queries and health checks.

5. **Review the report**. When the audit completes, the report appears as an expandable accordion in the chat thread. Findings are grouped by severity with color-coded badges:
   - Red for critical (stale data, failing refreshes, stale streams)
   - Orange for warning (approaching thresholds, suspended tasks)
   - Blue for info (best practice suggestions, architecture notes)

6. **Suggest fixes**. Click "Suggest Fix" on any finding to open a remediation chat. The agent provides SQL commands you can review and copy into a Snowflake worksheet.

### Local Development

For iterating on the app locally:

```bash
npm run dev
```

This starts the Next.js dev server at `http://localhost:3000`. Make sure your `.env.local` has `SNOWFLAKE_ACCOUNT` and `SNOWFLAKE_PAT` set.

<!-- ------------------------ -->
## Conclusion And Resources
Duration: 2

You have built a full-stack AI-powered pipeline auditor that runs on Snowflake App Runtime. The app uses a Cortex AI coding agent to autonomously discover pipeline objects, run health checks, and produce structured reports -- with an interactive fix suggestion workflow for remediation.

### What You Learned
- How to scaffold and deploy a Next.js app on Snowflake App Runtime with `snow app`
- How to use `@snowflake/cortex-agent-sdk` to run coding agent sessions that analyze your pipelines
- How to build composable system prompts that produce structured JSON reports
- How to create a poll-based architecture for real-time agent progress
- How to implement AI-powered fix suggestions with multi-turn chat

### Extending It
- **Schedule audits** with Snowflake Tasks for daily or weekly health reports
- **Send notifications** via `SYSTEM$SEND_EMAIL` when critical issues are found
- **Store audit history** in a Snowflake table for trend analysis over time
- **Add more scopes** like Snowpipe latency, warehouse queue depth, or credit anomalies

### Related Resources
- [@snowflake/cortex-agent-sdk on npm](https://www.npmjs.com/package/@snowflake/cortex-agent-sdk)
- [Snowflake App Runtime Documentation](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime)
- [Cortex Agents Overview](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Pipeline Auditor Companion Repository](https://github.com/sfc-gh-JCHAEARLEY/sfguide-pipeline-auditor-with-cortex-agent-sdk)

### Cleanup

To remove the demo objects created in this quickstart:

```sql
DROP DATABASE IF EXISTS PIPELINE_AUDITOR_DB;
-- Also drop the Application Service if deployed:
DROP APPLICATION SERVICE IF EXISTS pipeline_auditor;
```
