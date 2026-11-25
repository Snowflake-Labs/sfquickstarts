author: Myles Borins, Snowflake CoCo
id: build-a-chat-assistant-and-mcp-server-with-snowflake-app-runtime
summary: In a Snowsight workspace, give a Snowflake App Runtime app one set of tools, then serve them to an in-app chat assistant and to AI agents over MCP.
categories: snowflake-site:taxonomy/solution-center/certification/quickstart,snowflake-site:taxonomy/product/applications-and-collaboration,snowflake-site:taxonomy/product/ai,snowflake-site:taxonomy/snowflake-feature/build
environments: web
status: Published
language: en
duration: 40
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Build a Chat Assistant and MCP Server with Snowflake App Runtime
<!-- ------------------------ -->
## Overview

A [Snowflake App Runtime](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/about-snowflake-app-runtime) app can answer questions in two ways: through a chat box in the app, and through an MCP server that AI agents such as Snowflake CoCo call. In this guide you build Repo Radar, a small Next.js app on free GitHub star data that does both from one list of tools. Ask it which open source projects are trending, or how one repo's stars have grown.

You build, preview, and deploy the app in a Snowsight workspace, with nothing to install. You write each tool once. The chat route sends the tools to a model through the Cortex REST API and runs the ones it asks for. The MCP route serves the same tools to agents. Both run inside the app, with the app's sign-in and grants, so you don't create an agent object, an MCP server object, or an API key.

### What You'll Learn

* How to define an app's tools once, in `lib/tools.ts`
* How to build a chat assistant at `/api/chat` on the Cortex Chat Completions API
* How to serve the same tools over MCP at `/api/mcp`
* How to preview and deploy the app from Workspaces

### What You'll Build

A Next.js app with a `/chat` page that answers questions about trending GitHub repos, and an MCP server that agents can call.

### What You'll Need

* A Snowflake account with Snowflake App Runtime and workspace preview enabled
* A browser
* The free Snowflake Curated Data (Free) listing from Snowflake Marketplace
* Optional: [CoCo CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli) or [CoCo Desktop](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-desktop), to call the MCP server from an agent at the end

<!-- ------------------------ -->
## Get the Data

Repo Radar uses the GitHub Archive data in a free listing that Snowflake curates and maintains. `GITHUB_STARS` has the number of new stars each public repo got each day, and `GITHUB_REPOS` maps each repo ID to its `owner/name`.

1. Open the [Snowflake Curated Data (Free)](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255) listing in Snowflake Marketplace.
2. Select **Get**.
3. Keep the default database name, `SNOWFLAKE_CURATED_DATA_FREE`, and select **Get** again.

Getting a listing needs the `ACCOUNTADMIN` role or a role with the `IMPORT SHARE` privilege.

<!-- ------------------------ -->
## Create the App

1. In Snowsight, select **Workspaces**.
2. Create a new workspace and give it a name.
3. In the workspace, select **+ Add new » Next.js App**.
4. Keep the suggested project name.

Workspaces creates a Next.js project from the Snowflake App Runtime template. You'll use these parts of it:

* **lib/snowflake.ts** exports `snowflake`, the app's Snowflake client. It runs queries and calls account REST APIs with the app's credentials.
* **package.json** lists the app's packages.
* **app.yml** tells Snowflake how to build, run, and deploy the app.

### Add the packages

The app needs Zod, which describes each tool's arguments, and the MCP SDK. Open **package.json** and add two lines to `"dependencies"`:

```json
"@modelcontextprotocol/sdk": "^1.32.2",
"zod": "^4.6.7",
```

Preview installs packages when it starts, and again whenever `package.json` changes.

### Start Preview

In the file explorer, hover over your project folder and select the eye icon (**Open to full screen**). Preview starts the dev server and shows the starter app. Leave it open: each file you save reloads the app.

<!-- ------------------------ -->
## Define the Tools

In the file explorer, select **+** next to the **lib** folder and create **tools.ts**. Paste the following code. Each tool has a name, a description that tells a model when to use it, an argument schema, and a function that runs a query. The chat route and the MCP route both read this list.

```typescript
import { z } from "zod";
import { snowflake } from "@/lib/snowflake";

const DATA = "SNOWFLAKE_CURATED_DATA_FREE.PUBLIC_DATA_FREE";

export type Tool = {
  name: string;
  description: string;
  schema: z.ZodObject;
  run: (args: any, request: Request) => Promise<unknown>;
};

export const tools: Tool[] = [
  {
    name: "trending_repos",
    description:
      "Public GitHub repos that gained the most stars in the last `days` days, up to the latest " +
      "day in the data. Skips repos first seen in the last 90 days and repos that got stars on " +
      "fewer than a third of those days, which removes most star spam. Returns REPO_NAME " +
      "(owner/name), STARS gained, and LATEST_DAY.",
    schema: z.object({
      days: z.number().int().min(7).max(90).default(30),
      limit: z.number().int().min(1).max(25).default(10),
    }),
    run: async ({ days, limit }) => {
      const { rows } = await snowflake.query(
        `WITH latest AS (SELECT MAX(DATE) AS DAY FROM ${DATA}.GITHUB_STARS)
         SELECT r.REPO_NAME, SUM(s.COUNT) AS STARS, TO_VARCHAR(latest.DAY) AS LATEST_DAY
           FROM ${DATA}.GITHUB_STARS s
           JOIN ${DATA}.GITHUB_REPOS r USING (REPO_ID), latest
          WHERE s.DATE > DATEADD(day, -?, latest.DAY)
            AND r.FIRST_SEEN < DATEADD(day, -90, latest.DAY)
          GROUP BY r.REPO_NAME, latest.DAY
         HAVING COUNT(DISTINCT s.DATE) >= ? / 3
          ORDER BY STARS DESC
          LIMIT ?`,
        { binds: [days, days, limit] },
      );
      return rows;
    },
  },
  {
    name: "repo_stars",
    description:
      "New stars per week for one public GitHub repo, by week start date. Use the exact " +
      "owner/name, for example one returned by trending_repos.",
    schema: z.object({
      repo: z.string().regex(/^[\w.-]+\/[\w.-]+$/).describe("owner/name"),
      start: z.string().date().describe("ISO date"),
      end: z.string().date().describe("ISO date"),
    }),
    run: async ({ repo, start, end }) => {
      const { rows } = await snowflake.query(
        `SELECT TO_VARCHAR(DATE_TRUNC('week', s.DATE), 'YYYY-MM-DD') AS WEEK, SUM(s.COUNT) AS STARS
           FROM ${DATA}.GITHUB_STARS s
           JOIN ${DATA}.GITHUB_REPOS r USING (REPO_ID)
          WHERE r.REPO_NAME = ?
            AND s.DATE BETWEEN ? AND ?
          GROUP BY WEEK
          ORDER BY WEEK`,
        { binds: [repo, start, end] },
      );
      return rows;
    },
  },
];
```

Every argument goes into the SQL as a bind variable, never as text in the statement. A model writes these arguments, so treat them like any other user input.

The queries run with the app owner's rights, so everyone who opens the app gets the same answers. To run a tool as the signed-in user instead, query with `await asCaller()` from `@/lib/snowflake`. Preview has no caller's rights, so test those tools in the deployed app. See [Query Snowflake](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/query-snowflake).

<!-- ------------------------ -->
## Add the Chat Assistant

Create **app/api/chat/route.ts**: create the folders **api** and **chat** under **app**, then the file. For each question, the route sends the conversation and the tools to the [Cortex Chat Completions API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api), runs any tools the model asks for, and repeats until the model answers. `snowflake.fetch()` signs each request with the app's credentials.

```typescript
import { z } from "zod";
import { snowflake } from "@/lib/snowflake";
import { tools } from "@/lib/tools";

export const dynamic = "force-dynamic";

const MODEL = "claude-sonnet-5";
const MAX_TURNS = 5;
const MAX_RESULT_CHARS = 20_000;

const SYSTEM_PROMPT =
  "You answer questions about public GitHub repos from GitHub Archive star data. Use the " +
  "tools to look up figures, say which tool each figure came from, and give the latest day " +
  "the data covers. If the tools can't answer, say so.";

const requestSchema = z.object({
  messages: z
    .array(z.object({ role: z.enum(["user", "assistant"]), content: z.string().max(4_000) }))
    .min(1)
    .max(40),
});

const toolDefinitions = tools.map((tool) => ({
  type: "function",
  function: { name: tool.name, description: tool.description, parameters: z.toJSONSchema(tool.schema, { io: "input" }) },
}));

async function complete(messages: unknown[]) {
  const response = await snowflake.fetch("/api/v2/cortex/v1/chat/completions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: MODEL, messages, tools: toolDefinitions }),
  });
  if (!response.ok) {
    console.error("[chat] Cortex returned", response.status, (await response.text()).slice(0, 300));
    throw new Error("The model request failed");
  }
  const body = await response.json();
  return body.choices[0].message;
}

async function runTool(name: string, rawArgs: string, request: Request): Promise<string> {
  const tool = tools.find((t) => t.name === name);
  if (!tool) return JSON.stringify({ error: `Unknown tool: ${name}` });
  try {
    const args = tool.schema.parse(JSON.parse(rawArgs || "{}"));
    const text = JSON.stringify(await tool.run(args, request));
    return text.length > MAX_RESULT_CHARS ? text.slice(0, MAX_RESULT_CHARS) + " [result cut]" : text;
  } catch (e) {
    console.error(`[chat] ${name} failed`, e);
    return JSON.stringify({ error: "The tool failed. Try different arguments." });
  }
}

export async function POST(request: Request): Promise<Response> {
  const parsed = requestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return Response.json({ error: "Invalid request" }, { status: 400 });

  const messages: any[] = [{ role: "system", content: SYSTEM_PROMPT }, ...parsed.data.messages];
  try {
    for (let turn = 0; turn < MAX_TURNS; turn++) {
      const message = await complete(messages);
      if (!message.tool_calls?.length) return Response.json({ reply: message.content ?? "" });
      messages.push(message);
      for (const call of message.tool_calls) {
        console.log(`[chat] tool=${call.function.name}`);
        messages.push({
          role: "tool",
          tool_call_id: call.id,
          content: await runTool(call.function.name, call.function.arguments, request),
        });
      }
    }
    return Response.json({ reply: "I couldn't finish that answer. Try a narrower question." });
  } catch {
    return Response.json({ error: "The assistant is unavailable. Try again." }, { status: 502 });
  }
}
```

A few choices keep the loop safe and cheap:

* The route checks each tool's arguments against its schema before it runs the tool.
* A tool that fails returns an error to the model, which can then try different arguments.
* `MAX_TURNS` and `MAX_RESULT_CHARS` limit the work for each question.
* The browser sends the whole conversation each time, so the server keeps no state.

Now create **app/chat/page.tsx**, the chat page:

```tsx
"use client";

import { useState } from "react";

type Message = { role: "user" | "assistant"; content: string };

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!input.trim() || busy) return;
    const next: Message[] = [...messages, { role: "user", content: input.trim() }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next }),
      });
      const body = await response.json();
      setMessages([...next, { role: "assistant", content: body.reply ?? body.error }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl p-6">
      <h1 className="mb-4 text-2xl font-semibold">Repo Radar</h1>
      <div className="space-y-3">
        {messages.map((m, i) => (
          <p key={i} className={m.role === "user" ? "font-medium" : "whitespace-pre-wrap"}>
            {m.content}
          </p>
        ))}
        {busy && <p className="text-gray-500">Thinking...</p>}
      </div>
      <form onSubmit={send} className="mt-4 flex gap-2">
        <input
          className="flex-1 rounded border px-3 py-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Which repos are trending this month?"
        />
        <button className="rounded border px-4 py-2" disabled={busy}>
          Send
        </button>
      </form>
    </main>
  );
}
```

Finally, link to it from the home page. Open **app/page.tsx** and add this line inside the page's main content:

```tsx
<a href="/chat" className="underline">Ask Repo Radar</a>
```

### Try the chat

In Preview, select **Ask Repo Radar** and ask:

* "Which 5 repos gained the most stars in the last 30 days?"
* "Pick the top one and show its weekly stars since August."

The Preview logs show a `[chat] tool=` line for each tool the model called. The first question takes a few seconds while the warehouse resumes.

<!-- ------------------------ -->
## Add the MCP Server

Create **app/api/mcp/route.ts**. It registers every tool in the same list, and creates a new server for each request, so it works when App Runtime runs more than one copy of the app or restarts it.

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { tools } from "@/lib/tools";

export const dynamic = "force-dynamic";

function createServer(request: Request): McpServer {
  const server = new McpServer({ name: "repo-radar", version: "1.0.0" });
  for (const tool of tools) {
    server.registerTool(
      tool.name,
      { description: tool.description, inputSchema: tool.schema.shape },
      async (args) => {
        console.log(`[mcp] tool=${tool.name}`);
        try {
          const result = await tool.run(args, request);
          return { content: [{ type: "text", text: JSON.stringify(result) }] };
        } catch (e) {
          console.error(`[mcp] ${tool.name} failed`, e);
          return { content: [{ type: "text", text: "Query failed" }], isError: true };
        }
      },
    );
  }
  return server;
}

async function handle(request: Request): Promise<Response> {
  const server = createServer(request);
  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  await server.connect(transport);
  return transport.handleRequest(request);
}

// POST only: Next.js answers GET and DELETE with 405.
export const POST = handle;
```

The route has no API key check. App Runtime signs each caller in before a request reaches the deployed app, the same way it does for the app's pages. You'll call it once the app is deployed.

<!-- ------------------------ -->
## Deploy the App

Select **Deploy** above **app.yml**. The first deploy creates the `APPLICATION SERVICE` that runs your app and can take a few minutes. When it finishes, select **Open deployed app** from the menu next to **Deploy**, then select **Ask Repo Radar** and ask a question again.

The app's URL ends in `.snowflakecomputing.app`. The MCP server is at that URL plus `/api/mcp`.

### Share it

The role you deployed with owns the app. Anyone who uses the chat page or the MCP server needs usage on the app:

```sql
GRANT USAGE ON APPLICATION SERVICE <database>.<schema>.<app_name> TO ROLE ANALYST;
```

Apps in your personal database stay private to you. To share apps with other roles, an admin first runs app development setup from **Settings » Apps**.

<!-- ------------------------ -->
## Call the MCP Server from CoCo

This step is optional and runs on your own machine, in CoCo CLI or CoCo Desktop. Add the deployed server, with your app's URL and the name of a Snowflake CLI connection to the same account:

```bash
cortex mcp add repo-radar https://<app-host>/api/mcp --type http --snowflake-connection <connection>
```

`--snowflake-connection` tells CoCo to sign in with that connection, so you don't create or store a token. In CoCo CLI, new servers start turned off: enter `/mcp`, select `repo-radar`, and turn it on. CoCo Desktop reads the same `~/.snowflake/cortex/mcp.json` file. Start a new CoCo session and ask:

```text
Use the repo-radar tools to find this week's trending repos and
compare weekly stars for the top two since September.
```

CoCo calls `trending_repos`, then `repo_stars` twice. The chat page and CoCo use the same tools, so they get the same numbers.

<!-- ------------------------ -->
## Cleanup

In the menu next to **Deploy**, delete the deployed app, or ask CoCo in the workspace:

```text
Delete the deployed app for this project.
```

To remove the project too, delete its folder in Workspaces. If you added the MCP server to CoCo, remove it:

```bash
cortex mcp remove repo-radar
```

<!-- ------------------------ -->
## Conclusion And Resources

### What You Learned

* Define an app's tools once in `lib/tools.ts`
* Build a chat assistant on the Cortex Chat Completions API at `/api/chat`
* Serve the same tools to agents over MCP at `/api/mcp`
* Preview and deploy the app from a Snowsight workspace

Each model call uses Cortex REST API credits. See the [Snowflake Service Consumption Table](https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf).

### Related Resources

* [Build an MCP server](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/build-mcp-server)
* [Build a chat assistant](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/build-chat-assistant)
* [Develop in Snowsight Workspaces](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/workspaces)
* [Snowflake App Runtime Node.js SDK](https://docs.snowflake.com/en/developer-guide/snowflake-app-runtime/nodejs-sdk)
* [Cortex REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-rest-api)
* [Getting Started with Snowflake App Runtime](https://www.snowflake.com/en/developers/guides/getting-started-with-snowflake-app-runtime/)
* [Snowflake Curated Data (Free) listing](https://app.snowflake.com/marketplace/listing/GZTSZ290BV255)
