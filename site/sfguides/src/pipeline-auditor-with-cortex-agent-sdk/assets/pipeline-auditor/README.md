# Next.js Template for Snowflake Apps

Minimal Next.js app deployed as a Snowflake App. Queries Snowflake using the [Node.js SDK](https://docs.snowflake.com/en/developer-guide/node-js/nodejs-driver) and demonstrates server-side rendering, API routes, caller's-rights token handling, and secret access.

> **This README is the build guide for this template.** It is the authoritative, self-contained reference for what the template provides and how to modify its code to implement an application. The `snowflake-apps` skill scaffolds this template and then follows this README. Platform concerns that are the same for every template — generating `snowflake.yml` via `snow app setup`, `snow app deploy`, and post-deploy operations — are driven by the skill, not this file.

---

## What this template already provides (DO NOT recreate)

| File | Purpose |
|------|---------|
| `lib/snowflake.ts` | `querySnowflake` / `querySnowflakeLongRunning` (+ optional `{ callersRights: true }`) — SPCS OAuth, caller's-rights pooling, local-dev auth. Use long-running for heavy or slow SQL (see below). Also exports `getSecret(name, type)` for reading Snowflake `SECRET` values — see **Secrets** below. |
| `lib/constants.ts` | `APP_TITLE` and `LOGO_SRC` — shared between `app/layout.tsx` (metadata) and `components/app-header.tsx` (nav bar). Edit this file to rebrand. |
| `next.config.mjs` | Standalone output, unoptimized images, **and the Next.js workspace-root pin** (`turbopack.root` + `outputFileTracingRoot` set to `__dirname`). The pin is critical: Next.js 16 + Turbopack walks upward looking for a lockfile and silently re-roots the project if it finds one in a parent directory, which breaks `/` (404) and chunk URLs and corrupts `outputFileTracingRoot` at deploy time. **Do not remove the pin** when adding new config; merge with the existing object instead. |
| `public/icon.svg` | Default app icon used by browser metadata and the app's `icon` manifest field. **Replace this with a custom SVG that clearly represents the specific app being built.** |

Pre-installed capabilities you can rely on without setup:

- **API fetching** — `@tanstack/react-query` is pre-installed. Client components that fetch API routes should use `useQuery` (see `components/time-card.tsx`, `components/query-card.tsx`). The `QueryProvider` in `components/query-provider.tsx` wraps the root layout.
- **UI components** — shadcn/ui is pre-configured (`components.json`). `Button`, `Card`, `Alert`, `Badge`, `Separator`, and `Table` are already installed in `components/ui/`. Run `npx shadcn@latest add <component>` only for components not yet present.
- **Dark mode** — Built in via a custom theme provider in `components/theme-provider.tsx`. Respects the OS `prefers-color-scheme` setting by default. A Sun/Moon toggle in the header lets users override it. Light/dark CSS variable overrides live in `app/globals.css`.
- **Branding** — Edit `lib/constants.ts` to change the app title and logo path (shared by the header and page metadata). Edit the CSS variables in `app/globals.css` to change the primary brand color. Button colors and focus rings update automatically.

**Do NOT modify `lib/snowflake.ts` or `next.config.mjs` unless requirements demand it.** If you do edit `next.config.mjs`, also check for `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` in any parent directory of the app folder. If one exists, it will silently re-root the workspace and undo the workspace-root pin — warn the user.

---

## Implementing your app

Modify the scaffolded project **in one pass** to fully implement everything the user asked for. The template provides the skeleton; you fill in the real application.

**CRITICAL: NEVER use mock or hardcoded data. Every route/page must query real Snowflake tables.**

What you MUST create or modify:

1. **`app/page.tsx`** — Replace the demo page with the real application UI. This is a Server Component by default.
   - Use `export const dynamic = "force-dynamic"` on any page that queries Snowflake.
   - Import `querySnowflake` from `@/lib/snowflake` for server-side data fetching.
2. **`app/api/` routes** — Replace or add API route handlers for any data the frontend needs to fetch client-side.
   - Every route must use `querySnowflake()` or `querySnowflakeLongRunning()` with real SQL — no mocks. Prefer long-running for endpoints backed by slow or warehouse-heavy SQL (~10+ seconds).
   - Always include `export const dynamic = "force-dynamic"`.
3. **`app/layout.tsx`** — Update the page title and description to match the app.
4. **`app/globals.css`** — Replace or extend with styles appropriate for the application's aesthetic direction.
5. **Client Components** — Create as many `"use client"` components as needed. Place them in `app/` or `components/`.
   - Client components CANNOT import `querySnowflake()` directly. They must `fetch()` an API route.
6. **Additional libraries** — If the app needs charting, UI components, or icons, add them to `package.json` under `dependencies`. Good defaults:
   - **Charts**: `recharts` — see `components/chart-utils.tsx` (already in the template) for `getYAxisWidth` (prevents Y-axis label clipping) and `ChartTooltip` (readable tooltip on dark backgrounds).
   - **UI components**: `@shadcn/ui`
   - **Icons**: `lucide-react`
   - **Date handling**: `date-fns`
7. **`public/icon.svg`** — Replace the template/default SVG with a relevant custom app icon. This is required, not optional (see below).

### App icon requirement

Before finishing, update `public/icon.svg`. Do not leave the template/default icon in place.

- Generate a simple, original SVG icon that matches the app's domain, data, or primary workflow.
- Keep it self-contained in `public/icon.svg`; do not reference external fonts, images, or remote assets.
- Prefer readable shapes, restrained color, and a professional Snowflake Apps style over generic logos or decorative gradients.
- Verify `app/layout.tsx` still references `/icon.svg`, and that `app.yml` points at `public/icon.svg` — as `profile.icon` alongside a `snowflake.yml`, or as the top-level `icon` key in a `version: 2` manifest.

---

## `querySnowflake` vs `querySnowflakeLongRunning`

Import both from `@/lib/snowflake` when the app runs mixed workloads:

| Use | When |
|-----|------|
| **`querySnowflake`** | Default for **simple, fast** queries: small result sets, selective predicates, metadata lookups — anything expected to finish in **well under ~10 seconds**. |
| **`querySnowflakeLongRunning`** | SQL that may take **~10+ seconds**, or is **warehouse-heavy**: large table scans, heavy joins/aggregations, `COPY`/`GET`/`PUT`-style work, long procedures, or any statement where the warehouse may **resume** or work for a noticeable time before returning rows. |

Use `querySnowflakeLongRunning(sql, { callersRights: true })` when caller's rights apply to that slow path. Optional tuning: `pollIntervalMs`, `statusLogIntervalMs`, `maxWaitMs` (see `lib/snowflake.ts`).

---

## Auth modes: owner's rights vs caller's rights

Both modes can be used in the same app. Use `querySnowflake(sql)` for data the service can always access, and `querySnowflake(sql, { callersRights: true })` for data that must respect the calling user's permissions.

- **Owner's Rights**: queries run as the service identity. Use for shared/reference data that all users can see.
- **Caller's Rights**: queries run as the user who opened the app. Required for row-level security, column masking, or per-user data isolation. See [SPCS caller's rights docs](https://docs.snowflake.com/en/developer-guide/snowpark-container-services/tutorials/advanced/tutorial-7-callers-rights).

### Caller's rights needs no `app.yml` configuration

There is nothing to enable. Snowflake declares every App Runtime app caller's-rights-capable and injects the `sf-context-current-user-token` header on every ingress request. Do not add an `executeAsCaller` key to `app.yml` — `run:` accepts only `command`, and unknown keys are silently ignored, so it looks applied while doing nothing.

Two things are on you:

1. **Pass the option per query.** Owner's rights is the default for any call that omits it, so every query that must respect row access policies or masking needs `{ callersRights: true }` explicitly.
2. **Caller grants must exist on the app's owning role.** Without them, queries fail even though the calling user has access. See `references/permissions.md`.

If a caller's-rights query returns the wrong identity or no rows, see the troubleshooting section in `references/debugging.md`.

> **Local dev note:** The `sf-context-current-user-token` header is only injected by Snowflake in SPCS. When developing locally, caller's-rights queries warn and fall back to local dev credentials automatically.

---

## Code patterns

**Owner's Rights — Server Component:**
```typescript
import { querySnowflake } from "@/lib/snowflake"
export const dynamic = "force-dynamic"

export default async function Page() {
  const rows = await querySnowflake("SELECT * FROM DB.SCHEMA.LOOKUP_TABLE")
  return <div>{/* render rows */}</div>
}
```

**Owner's Rights — API route:**
```typescript
import { querySnowflake } from "@/lib/snowflake"
export const dynamic = "force-dynamic"

export async function GET() {
  const rows = await querySnowflake("SELECT ...")
  return Response.json(rows)
}
```

**Caller's Rights — Server Component:**
```typescript
import { querySnowflake } from "@/lib/snowflake"
export const dynamic = "force-dynamic"

export default async function Page() {
  const rows = await querySnowflake("SELECT * FROM DB.SCHEMA.SENSITIVE_TABLE", { callersRights: true })
  return <div>{/* render rows */}</div>
}
```

**Caller's Rights — API route:**
```typescript
import { querySnowflake } from "@/lib/snowflake"
export const dynamic = "force-dynamic"

export async function GET() {
  const rows = await querySnowflake("SELECT ...", { callersRights: true })
  return Response.json(rows)
}
```

**Bind parameters (always use for user-supplied values — prevents SQL injection):**
```typescript
import { querySnowflake } from "@/lib/snowflake"
export const dynamic = "force-dynamic"

export async function GET(req: Request) {
  const id = new URL(req.url).searchParams.get("id")
  // Use `?` placeholders and pass values via `binds` — never string-concatenate input into SQL.
  const rows = await querySnowflake(
    "SELECT * FROM DB.SCHEMA.ORDERS WHERE id = ?",
    { binds: [id] },
  )
  return Response.json(rows)
}
```

**Long-running or warehouse-heavy query (owner's or caller's rights):**
```typescript
import { querySnowflakeLongRunning } from "@/lib/snowflake"
export const dynamic = "force-dynamic"

export async function GET() {
  const rows = await querySnowflakeLongRunning(
    "SELECT ...", // e.g. heavy aggregation, COPY, or CALL long_job(...)
    { /* callersRights: true if needed */ }
  )
  return Response.json(rows)
}
```

**Client component consuming an API route (same for both auth modes):**
```typescript
"use client"
import { useEffect, useState } from "react"

export function DataTable() {
  const [data, setData] = useState([])
  useEffect(() => {
    fetch("/api/data").then(r => r.json()).then(setData)
  }, [])
  return <table>{/* render data */}</table>
}
```

**Critical error handling:**
```typescript
try {
   ...
} catch (e) {
  console.error(new Date().toISOString(), "[useful message]", e)
  return Response.json(
    { error: e instanceof Error ? e.message : "Failed to do something" },
    { status: 500 }
  )
}
```

---

## Design guidelines

- **Aesthetic**: Unless instructed otherwise, use your best judgement to choose an appropriate style for the app. By default, tend towards minimal, enterprise and professional design.
- **Color**: Brand colors (primary) are controlled by CSS variables in `app/globals.css`. Extend `globals.css` for palette tweaks.
- **Layout**: Be intentional about density; use consistent spacing.
- **Avoid**: Generic purple gradients, cookie-cutter layouts, raw HTML elements when a UI library is available.

---

## Local development

```bash
npm install
npm run dev
```

The app reads Snowflake credentials automatically from your default [Snowflake CLI](https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/specify-credentials) connection in `~/.snowflake/config.toml`. No extra configuration needed if you already have `snow` CLI set up.

To use a specific named connection, set `SNOWFLAKE_CONNECTION_NAME`:

```bash
SNOWFLAKE_CONNECTION_NAME=myconn npm run dev
```

Alternatively, skip the config file entirely and provide env vars directly:

```bash
SNOWFLAKE_ACCOUNT=myaccount \
SNOWFLAKE_ACCOUNT_URL=https://myaccount.snowflakecomputing.com \
SNOWFLAKE_USER=myuser \
SNOWFLAKE_PASSWORD=mypassword \
SNOWFLAKE_WAREHOUSE=my_wh \
npm run dev
```

The app runs at `http://localhost:<port>` (read the actual port from the dev-server output — Next.js auto-increments away from 3000 when busy). On first API request, the browser opens for Snowflake SSO authentication.

Start the dev server **in the background** — it's a long-running process.

### Two valid local-preview commands, one anti-pattern

| Command | When to use |
|---------|-------------|
| `npm run dev` (`next dev`) | Iterative development with hot reload. Default choice for code changes. |
| `npm run start` (`next start`) | Production-mode preview before deploy — useful when you want to test against the same code path Next.js will run in production. |
| ❌ `node .next/standalone/server.js` | **Never use this for local preview.** |

**Why `node .next/standalone/server.js` is wrong locally:** The standalone server is a deployment artifact for the Snowflake App Runtime container image — it serves *only* the minimum needed at runtime and does **not** serve `.next/static` or `/public`. Symptoms when you run it locally: pages render unstyled, all `/_next/static/chunks/*.js|*.css` return 404, client components never hydrate so the UI stays on "Loading…". Reserve the standalone server for deploy verification, not iteration.

### Dev-server output signatures to watch for

`next dev` prints compile and request problems to the shell it runs in. After it starts, and after each edit that triggers a recompile, read that output and act on these signatures:

| Signature in the output | What it means | Where to look |
|-------------------------|---------------|---------------|
| `Failed to compile` | TypeScript/JSX build error — the page won't render until fixed | The file + line in the block right below it |
| `Module not found: Can't resolve '…'` | Bad import path or a missing dependency | Fix the import, or add the package to `package.json` and re-`npm install` |
| `Type error:` / `TS####:` | TypeScript type error | The cited file:line |
| Lines beginning `    at ` | A runtime stack trace — read upward past the framework frames | The first frame pointing into `app/`, `components/`, or `lib/` |
| `GET /… 500` (or a `500` on an `/api/*` line) | A server-side crash in a route/page | The `[snowflake]` / `console.error` lines just above it — usually auth, a missing grant, or wrong warehouse |
| `⨯` prefix | Next.js error marker for the line that follows | The message after the marker |

Distinguish these from benign noise that resolves on its own: `✓ Compiled`, hot-reload / Fast Refresh notices, and the one-time SSO browser prompt on the first Snowflake query are **not** failures. A `500` seen while you're mid-edit may clear once the recompile finishes — confirm it persists before chasing it.

### Verify before declaring success

After starting a local preview (either `npm run dev` or `npm run start`), run all three checks and confirm they pass before reporting back to the user:

```bash
# 1. Homepage returns 200 with non-empty body
curl -fsS http://localhost:<port>/ | head -c 200

# 2. At least one /api/* route returns 200 with JSON
curl -fsS http://localhost:<port>/api/<your-route>

# 3. Static chunks resolve (catches the standalone-server / re-rooted-workspace bugs)
curl -fsS -o /dev/null -w "%{http_code}\n" http://localhost:<port>/_next/static/chunks/<any-chunk>.js
```

If any check fails — particularly chunks 404'ing — diagnose before telling the user the app is up. Common causes:

- **404 on `/_next/static/chunks/*`**: you ran the standalone server (use `next dev` / `next start` instead) **or** `next.config.mjs` lost its `turbopack.root` / `outputFileTracingRoot` pin and Turbopack re-rooted to a parent directory with a stray lockfile. Re-pin and rebuild.
- **404 on `/`**: same re-root cause (chunk URLs end up under `/<app-dir>/app/...`).
- **API route returns 500**: look at the dev-server output for the specific Snowflake error — typically auth, missing grant, or wrong warehouse.

---

## Testing

The template ships with [Vitest](https://vitest.dev/) pre-wired and working example tests in `__tests__/` — extend these rather than introducing a different test runner.

| File | What it covers |
|------|-----------------|
| `vitest.config.ts` | Node environment, `@` path alias |
| `__tests__/lib/snowflake.test.ts` | Unit tests for `getSecret` across all three `SecretType`s: mounted-file vs env-var fallback, OAuth2 refresh/caching |
| `__tests__/api/query.test.ts`, `__tests__/api/time.test.ts` | Route-handler tests that mock `querySnowflake` and assert on the `Response` shape |

```bash
npm test   # vitest run
```

**Pattern: mock `lib/snowflake`, test everything around it.** Don't hit real Snowflake in unit tests. `vi.mock("../../lib/snowflake", () => ({ querySnowflake: vi.fn() }))` and assert on route logic, response shape, and error handling, following `query.test.ts`. This keeps tests fast and deterministic.

**Code coverage** is standard Vitest, not a Snowflake-specific feature — add `@vitest/coverage-v8` and a `coverage` block to `vitest.config.ts` if the project needs it; nothing here configures thresholds for you.

**Integration tests against real Snowflake data** run the same way local dev does: `npm run dev` / `npm run start` already authenticate through the developer's `snow` CLI connection (see Local development above), so integration-style tests can call the running app's routes and hit real tables. For a staged environment, declare `dev`/`stage`/`prod` `targets` in `app.yml` (see `references/manifests.md`) and run integration tests against the `dev`/`stage` URL before promoting to `prod`.

**Pre-deploy sanity checks** (manifest and bundle correctness, not app logic) don't require a deploy:

```bash
snow app validate   # confirms the target database/schema resolve and the project can be bundled
snow app bundle     # copies resolved artifacts to ./output/bundle so you can inspect what would be uploaded
```

**CI/CD**: `snow app deploy` is a standard CLI command callable from any pipeline. The common pattern is `npm ci && npm test` (plus `snow app validate`) as a gate before `snow app deploy --target <name>`, authenticating via OIDC (workload identity federation) rather than long-lived credentials. Don't hand-write this: use the `ci-cd` skill for the full setup on GitHub Actions, GitLab CI, or Azure DevOps — service user, network policy, secrets, checkpoints, and verification. It detects this as a Snowflake App Runtime project and pulls the deploy-step content (which `snow app deploy` phase/target to run) from `references/cicd.md`.

---

## API route pitfalls

### Snowflake JS SDK returns TIMESTAMP columns as Date objects, not strings

The Snowflake Node.js SDK returns `TIMESTAMP_LTZ`, `TIMESTAMP_NTZ`, and `TIMESTAMP_TZ` columns as **JavaScript `Date` objects**, not ISO strings. `String(jsDate)` produces locale-style output like `"Tue Jun 03 2026 09:14:52 GMT+0000 (UTC)"`, which:

- **Breaks display** — `.slice(0, 10)` gives `"Tue Jun 03"` instead of `"2026-06-03"`.
- **Breaks sorting** — comparing month names alphabetically (`"May" > "Jun"`) inverts chronological order.

**Always normalise at the API boundary before mapping to a response field:**

```ts
function toIso(val: unknown): string | null {
  if (!val) return null
  if (val instanceof Date) return val.toISOString()  // "2026-06-03T09:14:52.000Z"
  return String(val)
}

// In your row mapper:
createdOn: toIso(row.CREATED_ON)?.slice(0, 10) ?? null,  // "2026-06-03" for display
publishedOn: toIso(row.UPDATED_ON),                       // full ISO for sort precision
```

If you need only the date portion for display, use `.slice(0, 10)` on the ISO string. If you also need to sort by time within the same calendar day, keep the full ISO string and only trim it when rendering.

This applies to **every** API route that maps timestamp columns. Check `CREATED_ON`, `UPDATED_ON`, `DELETED_ON`, and any other timestamp fields.

---

## Secrets

How this template reads sensitive values (API keys, username/password credentials, OAuth2 tokens) at runtime, both locally and in SPCS.

### Golden rule

**Always read secrets through `getSecret(name, type)` from `@/lib/snowflake`.** Do NOT:

- Read `process.env.SNOWFLAKE_SECRET_*` directly — `getSecret` prefers the mounted secret file in SPCS and only falls back to the env var for local dev; reading the env var yourself skips the mounted file.
- Query the `SECRET` object at runtime (e.g. `SYSTEM$GET_SECRET`, `SELECT ... FROM SECRET`) — this is insecure and not supported in app code.

`getSecret` already abstracts the local-dev vs SPCS difference, so the same app code works in both environments. Call it only in server code (Server Components or API route handlers) — never expose a secret value to a client component or include it in a response sent to the browser.

### API

```typescript
import { getSecret, SecretType } from "@/lib/snowflake"

const apiKey = getSecret("API_KEY", SecretType.GENERIC_STRING)            // => string
const { username, password } = getSecret("DB_CREDS", SecretType.PASSWORD) // => { username, password }
const token = await getSecret("MY_OAUTH", SecretType.OAUTH2)             // => string (async — await it)
```

### Supported secret types

`GENERIC_STRING`, `PASSWORD`, and `OAUTH2` are supported.

| `SecretType` | Returns | Mounted file(s) in SPCS | Env-var fallback (local dev) |
|--------------|---------|--------------------------|------------------------------|
| `GENERIC_STRING` | `string` | `/secrets/<name>/secret_string` | `SNOWFLAKE_SECRET_<NAME>_SECRET_STRING` |
| `PASSWORD` | `{ username, password }` | `/secrets/<name>/username`, `/secrets/<name>/password` | `SNOWFLAKE_SECRET_<NAME>_USERNAME`, `SNOWFLAKE_SECRET_<NAME>_PASSWORD` |
| `OAUTH2` | `Promise<string>` (async — `await` it) | `/secrets/<name>/access_token` (auto-rotated) | client-credentials refresh flow (see [Local development setup](#local-development-setup)) |

> **`OAUTH2` is async** — `getSecret(name, SecretType.OAUTH2)` returns a `Promise<string>`, so you must `await` it (`GENERIC_STRING` and `PASSWORD` are synchronous). OAuth tokens expire in minutes: in SPCS `getSecret` reads the auto-rotated mounted token fresh on every call; locally it mints and refreshes tokens via the OAuth2 client-credentials grant (cached in memory, refreshed just before expiry).

### Resolution order

For `GENERIC_STRING` / `PASSWORD` fields, `getSecret`:

1. Reads the **mounted file** `/secrets/<name>/<field>` (present in SPCS). `<name>` matches the `secrets[].name` in `app.yml`.
2. If the file is absent/empty (e.g. local dev), falls back to the **env var** `SNOWFLAKE_SECRET_<NAME>_<FIELD>` (upper-cased).
3. If neither is available, throws a descriptive error.

The env-var name is always upper-cased, so `getSecret("api_key", ...)` and `getSecret("API_KEY", ...)` resolve to the same fallback env var.

### Required: declare the secret in `app.yml`

For a secret to be mounted in SPCS, it MUST be listed under `secrets:` in `app.yml`. Each entry maps a logical name (used in `getSecret`) to a fully-qualified Snowflake `SECRET` object.

> **CRITICAL — `secrets:` is a TOP-LEVEL key.** It is a sibling of `install:` and `run:` — at column 0. **Do NOT nest it under `run:`** (next to `command:`). A `secrets:` block placed under `run:` is ignored and the secret will not be mounted in SPCS. The same applies to the top-level `environment_variables:` block. This placement is identical in both manifest layouts.

Here is a complete `app.yml` showing the correct placement (note `secrets:` and `environment_variables:` are at the same indentation level as `install:`/`run:`):

```yaml
install:
  commands:
    - ["npm", "ci", "--include=dev"]

run:
  command: ["node", ".next/standalone/server.js"]

profile:                              # ← build-only manifest (paired with snowflake.yml);
  label: "My App"                     #   in a `version: 2` manifest these are top-level
  description: "..."                  #   `label:` / `description:` / `icon:` keys instead

secrets:                              # ← top-level, NOT under run:
  - name: SOME_API_KEY
    secret: DB.SCHEMA.API_KEY
  - name: SOME_USER_PASS
    secret: DB.SCHEMA.API_KEY_2

environment_variables:               # ← also top-level (non-secret config)
  - name: SOME_ENV_TEST
    value: "PIZZA"
  - name: LOG_LEVEL
    value: "INFO"
```

- `name`: the logical name passed to `getSecret` (e.g. `getSecret("SOME_API_KEY", ...)`) and the directory name under `/secrets/`.
- `secret`: the fully-qualified name of an existing Snowflake `SECRET` object. In a `version: 2` manifest a bare name is also accepted and is qualified with the app's database and schema.
- Non-secret configuration goes under `environment_variables:` (plain `name`/`value` pairs), not `secrets:`.

If a secret is used in code but missing from `app.yml`, the app will work locally (if the fallback env var is set) but fail in SPCS. Always keep `app.yml` `secrets:` in sync with the `getSecret` calls in the code. In a `version: 2` manifest this cuts both ways: the deploy is declarative, so removing a secret from the manifest also unmounts it from the running service on the next deploy.

For the full list of accepted `app.yml` keys, see `references/debugging.md` (build-only manifest) and `references/manifests.md` (`version: 2` manifest).

### Local development setup

In SPCS the runtime mounts each secret as files under `/secrets/<name>/`. Locally there are no mounted files, so provide the fallback env vars yourself, typically in `.env.local` (already git-ignored):

```bash
# GENERIC_STRING
SNOWFLAKE_SECRET_SOME_API_KEY_SECRET_STRING=sk-local-dev-key

# PASSWORD
SNOWFLAKE_SECRET_SOME_USER_PASS_USERNAME=local_user
SNOWFLAKE_SECRET_SOME_USER_PASS_PASSWORD=local_pass

# OAUTH2 — client-credentials refresh flow (recommended; auto-refreshes before expiry)
SNOWFLAKE_SECRET_MY_OAUTH_OAUTH_TOKEN_URL=https://provider.example.com/oauth2/token
SNOWFLAKE_SECRET_MY_OAUTH_OAUTH_CLIENT_ID=local-client-id
SNOWFLAKE_SECRET_MY_OAUTH_OAUTH_CLIENT_SECRET=local-client-secret
SNOWFLAKE_SECRET_MY_OAUTH_OAUTH_SCOPE=api.read        # optional
# OAUTH2 — OR a static short-lived token (no auto-refresh; expires):
# SNOWFLAKE_SECRET_MY_OAUTH_ACCESS_TOKEN=eyJhbGci...
```

### Secret scenarios

**1. Use secrets while creating a new app** — Implement the reads with `getSecret`, declare every secret under `secrets:` in `app.yml`, and tell the user which `SECRET` objects must exist in their account (and to set the fallback env vars for `npm run dev`). The skill does not create the `SECRET` object itself — see scenario 3.

**2. Read an existing secret in an existing app**
1. Confirm the secret name and type (`GENERIC_STRING`, `PASSWORD`, or `OAUTH2`).
2. Add the `getSecret(name, type)` call in the relevant server code (`await` it for `OAUTH2`). If the code currently reads `process.env.SNOWFLAKE_SECRET_*` or queries the `SECRET` object directly, replace it with `getSecret`.
3. Ensure the secret is declared under `secrets:` in `app.yml`.
4. Remind the user to set the matching fallback env var(s) for local dev.

**3. Create a new secret** — **Delegate the creation of the `SECRET` object to Coco** (Cortex Code) — do not author `CREATE SECRET` SQL as part of this skill. Once the secret exists in Snowflake, the **usage** in the app is this template's job:
1. Add it to `app.yml` under `secrets:` (`name` + fully-qualified `secret`).
2. Read it in code with `getSecret`.
3. Set the fallback env var(s) so it works under `npm run dev`.

---

## Deploy

Deployment is driven by the `snowflake-apps` skill, not this template. It generates the deployment manifest via `snow app setup` — either a `snowflake.yml` paired with this build-only `app.yml`, or a single `app.yml` with `version: 2` that absorbs both — configures the app's display metadata, and runs `snow app deploy`. Once deployed, the app is reachable at its `.snowflakecomputing.app` endpoint URL.
