/**
 * Audit engine — JSON schema, system prompt sections, and prompt builder.
 * Ported from the original Express server to work with Next.js API routes.
 */

// ---------------------------------------------------------------------------
// Audit report JSON schema (matches Python schemas.py)
// ---------------------------------------------------------------------------
export const AUDIT_REPORT_SCHEMA = {
  type: "object",
  properties: {
    database: { type: "string" },
    audit_timestamp: { type: "string" },
    pipeline_inventory: {
      type: "object",
      properties: {
        schemas: { type: "array", items: { type: "string" } },
        tables: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
              type: { type: "string" },
              row_count: { type: "number" },
            },
            required: ["schema", "name", "type"],
          },
        },
        dynamic_tables: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
              target_lag: { type: "string" },
              refresh_mode: { type: "string" },
              scheduling_state: { type: "string" },
            },
            required: ["schema", "name"],
          },
        },
        tasks: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
              schedule: { type: "string" },
              state: { type: "string" },
            },
            required: ["schema", "name"],
          },
        },
        views: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
            },
            required: ["schema", "name"],
          },
        },
        streams: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
              source_type: { type: "string" },
              table_name: { type: "string" },
              mode: { type: "string" },
              stale: { type: "boolean" },
              stale_after: { type: "string" },
            },
            required: ["schema", "name"],
          },
        },
        pipes: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
              definition: { type: "string" },
              is_autoingest: { type: "boolean" },
              notification_channel: { type: "string" },
            },
            required: ["schema", "name"],
          },
        },
        procedures: {
          type: "array",
          items: {
            type: "object",
            properties: {
              schema: { type: "string" },
              name: { type: "string" },
              language: { type: "string" },
              arguments: { type: "string" },
            },
            required: ["schema", "name"],
          },
        },
      },
      required: ["schemas", "tables", "dynamic_tables", "tasks", "views"],
    },
    findings: {
      type: "array",
      items: {
        type: "object",
        properties: {
          category: {
            type: "string",
            enum: [
              "freshness",
              "volume",
              "schema",
              "dt_health",
              "task_status",
              "data_quality",
              "pipeline_design",
              "stream_health",
              "pipe_status",
              "procedure_review",
            ],
          },
          severity: {
            type: "string",
            enum: ["critical", "warning", "info"],
          },
          object: { type: "string" },
          message: { type: "string" },
          details: { type: "object" },
        },
        required: ["category", "severity", "object", "message"],
      },
    },
    summary: {
      type: "object",
      properties: {
        total_objects: { type: "number" },
        critical: { type: "number" },
        warning: { type: "number" },
        info: { type: "number" },
        overall_health: {
          type: "string",
          enum: ["healthy", "needs_attention", "unhealthy"],
        },
      },
      required: [
        "total_objects",
        "critical",
        "warning",
        "info",
        "overall_health",
      ],
    },
  },
  required: [
    "database",
    "audit_timestamp",
    "pipeline_inventory",
    "findings",
    "summary",
  ],
};

// ---------------------------------------------------------------------------
// System prompt — composable sections keyed by audit scope
// ---------------------------------------------------------------------------
export const PROMPT_PREAMBLE_ALL_SCHEMAS = `You are a Snowflake Data Pipeline Auditor. Your job is to comprehensively audit
a database's data pipeline by examining its objects, freshness, health, and quality.

WORKFLOW:
1. DISCOVER: Run the discovery queries below to build a complete pipeline inventory.
   - Schemas: SHOW SCHEMAS IN DATABASE <DATABASE>;`;

export const PROMPT_PREAMBLE_SINGLE_SCHEMA = `You are a Snowflake Data Pipeline Auditor. Your job is to comprehensively audit
a specific schema's data pipeline by examining its objects, freshness, health, and quality.

CRITICAL CONSTRAINT: You are auditing ONLY the <SCHEMA> schema in the <DATABASE> database.
- NEVER run SHOW SCHEMAS. The schema is already known: <SCHEMA>.
- NEVER audit objects outside <DATABASE>.<SCHEMA>.
- All SHOW commands must use IN SCHEMA <DATABASE>.<SCHEMA> (not IN DATABASE).
- All INFORMATION_SCHEMA queries must filter with WHERE table_schema = '<SCHEMA>'.

WORKFLOW:
1. DISCOVER: Run the discovery queries below scoped to <DATABASE>.<SCHEMA>. Skip schema discovery — go directly to object discovery.`;

export const PROMPT_SECTIONS: Record<string, string> = {
  tables_freshness: `
TABLES & FRESHNESS:
   - Tables and row counts:
     SELECT table_schema, table_name, table_type, row_count
     FROM <DATABASE>.INFORMATION_SCHEMA.TABLES
     WHERE table_schema NOT IN ('INFORMATION_SCHEMA')
     ORDER BY table_schema, table_name;
   - Check freshness — identify stale tables:
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
   - Check refresh history for failures:
     SELECT name, state, state_message, refresh_start_time, refresh_end_time,
            DATEDIFF('second', refresh_start_time, refresh_end_time) AS duration_sec
      FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(NAME_PREFIX => '<DT_NAME_PREFIX>'))
      ORDER BY refresh_start_time DESC LIMIT 20;`,

  tasks: `
TASKS:
   - Discover: SHOW TASKS IN DATABASE <DATABASE>;
   - Check execution history for failures via TASK_HISTORY table function
   - Flag suspended tasks and tasks with recent failures`,

  views: `
VIEWS:
   - Discover views from INFORMATION_SCHEMA.TABLES WHERE table_type = 'VIEW'
   - Note materialized vs standard views`,

  streams: `
STREAMS:
   - Discover: SHOW STREAMS IN DATABASE <DATABASE>;
   - Check each stream's stale status (stale = true means the stream offset has fallen behind
     and data may be lost — this is CRITICAL)
   - Check stale_after timestamp — if it's approaching, flag as warning
   - Check mode (DEFAULT, APPEND_ONLY, INSERT_ONLY) and source_type
   - Flag streams on dropped or non-existent tables`,

  pipes: `
PIPES:
   - Discover: SHOW PIPES IN DATABASE <DATABASE>;
   - Check pipe status (RUNNING, STOPPED_CLONING, PAUSED, STALLED)
   - Check recent copy history for errors:
     SELECT pipe_name, file_name, status, first_error_message, first_error_line_number,
            last_load_time, row_count, row_parsed, error_count
     FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
       TABLE_NAME => '<DATABASE>.*',
       START_TIME => DATEADD('day', -7, CURRENT_TIMESTAMP())
     ))
     WHERE status != 'Loaded'
     ORDER BY last_load_time DESC LIMIT 30;
   - Flag pipes with high error rates or that are paused/stalled`,

  procedures: `
STORED PROCEDURES:
   - Discover: SHOW PROCEDURES IN DATABASE <DATABASE>;
   - Identify ETL-related procedures (look for INSERT, MERGE, COPY, CREATE TABLE AS patterns
     in procedure names or definitions)
   - Note the language (SQL, JavaScript, Python, Java, Scala) and whether they appear to be
     scheduled via tasks
   - Flag procedures that seem to be doing data movement but have no associated task (orphaned ETL)`,
};

export const PROMPT_FOOTER = `
FINDING SEVERITY GUIDE:
- critical: Data stale beyond 7x threshold, DTs failing, tasks suspended, streams stale, pipes with errors
- warning: Data aging beyond threshold, DT lag exceeding target, design issues, approaching stale streams
- info: Observations, best practice suggestions, pipeline architecture notes

Replace <DATABASE> with the actual database name provided by the user.
Be thorough. Check every schema, every object type in scope. The user needs a complete picture.

For any object types NOT in scope, set their inventory arrays to empty arrays [] and skip those checks.`;

export function buildSystemPrompt(
  database: string,
  scope: string[],
  schema: string,
): string {
  const allScopes = Object.keys(PROMPT_SECTIONS);
  const activeScopes = scope.length > 0 ? scope : allScopes;

  let prompt = schema
    ? PROMPT_PREAMBLE_SINGLE_SCHEMA
    : PROMPT_PREAMBLE_ALL_SCHEMAS;
  for (const key of allScopes) {
    if (activeScopes.includes(key)) {
      prompt += PROMPT_SECTIONS[key];
    }
  }
  prompt += PROMPT_FOOTER;

  // Replace placeholders
  prompt = prompt.replace(/<DATABASE>/g, database);
  const dtPrefix = schema ? `${database}.${schema}.` : `${database}.`;
  prompt = prompt.replace(/<DT_NAME_PREFIX>/g, dtPrefix);

  if (schema) {
    prompt = prompt
      .replace(/<SCHEMA>/g, schema)
      .replace(
        new RegExp(`SHOW (\\w+(?:\\s+\\w+)?) IN DATABASE ${database}`, "g"),
        `SHOW $1 IN SCHEMA ${database}.${schema}`,
      )
      .replace(
        /WHERE table_schema NOT IN \('INFORMATION_SCHEMA'\)/g,
        `WHERE table_schema = '${schema}'`,
      )
      .replace(
        /Be thorough\. Check every schema, every object type in scope\./,
        `Be thorough. Check every object type in scope within the ${schema} schema.`,
      );
  }

  return prompt;
}

export const SCOPE_LABELS: Record<string, string> = {
  tables_freshness: "tables & freshness",
  dynamic_tables: "dynamic tables",
  tasks: "tasks",
  views: "views",
  streams: "streams",
  pipes: "pipes",
  procedures: "stored procedures",
};

export function buildAuditUserPrompt(
  database: string,
  scope: string[],
  schema: string,
): string {
  const activeScope =
    scope.length > 0 ? scope : Object.keys(PROMPT_SECTIONS);
  const scopeDesc = activeScope
    .map((s: string) => SCOPE_LABELS[s] || s)
    .join(", ");
  const schemaClause = schema
    ? ` Only audit the ${database}.${schema} schema — do NOT run SHOW SCHEMAS or look at any other schema.`
    : "";
  return schema
    ? `Run a comprehensive pipeline audit on ${database}.${schema}. Scope: ${scopeDesc}.${schemaClause} Run the checks described in the system prompt for each scope area directly against ${database}.${schema} and return the full structured audit report.`
    : `Run a comprehensive pipeline audit on the ${database} database. Scope: ${scopeDesc}. Discover all in-scope objects, run the checks described in the system prompt for each scope area, and return the full structured audit report.`;
}
