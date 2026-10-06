import { NextRequest, NextResponse } from "next/server";
import { createAgentClient } from "@/lib/agent-client";
import {
  buildSystemPrompt,
  buildAuditUserPrompt,
} from "@/lib/audit-engine";
import { jobStore, pushJobEvent } from "@/lib/audit-store";

export const dynamic = "force-dynamic";

// Keep reference to the active audit thread messages for follow-up chat
const g = globalThis as Record<string, unknown>;
if (!g.__auditThreadMessages) {
  g.__auditThreadMessages = [] as Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }>;
}
function getAuditThread(): Array<{
  role: string;
  content: Array<{ type: string; text: string }>;
}> {
  return g.__auditThreadMessages as Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }>;
}
function setAuditThread(
  messages: Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }>,
) {
  g.__auditThreadMessages = messages;
}

export { getAuditThread, setAuditThread };

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const {
    database = "",
    scope = [],
    schema = "",
  } = body as {
    database?: string;
    scope?: string[];
    schema?: string;
  };

  const jobId = `audit-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  jobStore.set(jobId, { events: [], done: false });

  pushJobEvent(jobId, {
    type: "status",
    message: "Starting audit session...",
    database,
    _ts: Date.now(),
  });

  // Return immediately — audit runs in background
  const response = NextResponse.json({ jobId });

  // Fire and forget
  runAuditJob(jobId, database, scope, schema).catch((err) => {
    console.error("Audit job error:", err);
  });

  return response;
}

async function runAuditJob(
  jobId: string,
  database: string,
  scope: string[],
  schema: string,
) {
  const job = jobStore.get(jobId);
  if (!job) return;

  const toolCounter = { count: 0, start: Date.now() };

  try {
    const client = createAgentClient();
    const systemPrompt = buildSystemPrompt(database, scope, schema);
    const userPrompt = buildAuditUserPrompt(database, scope, schema);

    pushJobEvent(jobId, {
      type: "status",
      message: "Session connected. Running audit...",
    });

    // Build message history for the audit
    const messages = [
      {
        role: "user" as const,
        content: [
          { type: "text" as const, text: systemPrompt + "\n\n" + userPrompt },
        ],
      },
    ];

    // Store for follow-up chat
    setAuditThread([...messages]);

    const stream = client.codingAgent.stream({
      permissionPolicy: "always_allow",
      messages,
    });

    let report: unknown = null;
    let reportEmitted = false;
    let accumulatedText = "";

    for await (const event of stream) {
      const ev = event as Record<string, unknown>;

      // Handle delta events from the stream
      if (ev.delta) {
        const delta = ev.delta as Record<string, unknown>;
        if (delta.content && Array.isArray(delta.content)) {
          for (const item of delta.content) {
            const block = item as Record<string, unknown>;

            if (block.type === "text" && block.text) {
              accumulatedText += String(block.text);

              // Try to parse accumulated text as JSON report
              try {
                const parsed = JSON.parse(accumulatedText);
                if (parsed.findings) {
                  report = parsed;
                  reportEmitted = true;
                  pushJobEvent(jobId, { type: "report", report: parsed });
                  pushJobEvent(jobId, {
                    type: "result",
                    isError: false,
                    numTurns: 0,
                    durationMs: Date.now() - toolCounter.start,
                    toolCalls: toolCounter.count,
                  });
                }
              } catch {
                // Not complete JSON yet — continue accumulating
              }
            } else if (block.type === "tool_use") {
              toolCounter.count++;
              const elapsed = (
                (Date.now() - toolCounter.start) /
                1000
              ).toFixed(1);
              const toolName = String(block.name || "unknown");
              const toolInput = block.input as
                | Record<string, unknown>
                | undefined;

              const progressEvent: Record<string, unknown> = {
                type: "tool_progress",
                toolName,
                count: toolCounter.count,
                elapsed: Number(elapsed),
              };

              if (toolName === "sql_execute" && toolInput) {
                progressEvent.sqlPreview = String(toolInput.sql || "")
                  .slice(0, 120)
                  .replace(/\n/g, " ");
                progressEvent.description = toolInput.description || "";
              }

              pushJobEvent(jobId, progressEvent);
              pushJobEvent(jobId, {
                type: "tool_use",
                toolName,
                toolId: block.id || "",
                input: toolInput || {},
              });
            } else if (block.type === "thinking") {
              pushJobEvent(jobId, {
                type: "thinking",
                text: block.thinking || block.text || "",
              });
            }
          }
        }
      }

      // Handle top-level event types
      if (ev.type === "message_stop" || ev.type === "content_block_stop") {
        // Try to parse any remaining accumulated text
        if (!report && accumulatedText.trim()) {
          try {
            const parsed = JSON.parse(accumulatedText);
            if (parsed.findings) {
              report = parsed;
              reportEmitted = true;
              pushJobEvent(jobId, { type: "report", report: parsed });
            }
          } catch {
            // Not JSON
          }
        }
      }

      if (reportEmitted) break;
    }

    // If we never got a report from text, try the final accumulated text
    if (!report && accumulatedText.trim()) {
      try {
        const parsed = JSON.parse(accumulatedText.trim());
        if (parsed.findings) {
          report = parsed;
          pushJobEvent(jobId, { type: "report", report: parsed });
        }
      } catch {
        // Not valid JSON
      }
    }

    // Emit final result if not already done
    if (!reportEmitted) {
      pushJobEvent(jobId, {
        type: "result",
        isError: !report,
        numTurns: 0,
        durationMs: Date.now() - toolCounter.start,
        toolCalls: toolCounter.count,
        ...(report ? { report } : {}),
      });
    }

    // Store the assistant response in thread for follow-up chat
    if (accumulatedText) {
      const thread = getAuditThread();
      thread.push({
        role: "assistant",
        content: [{ type: "text", text: accumulatedText }],
      });
      setAuditThread(thread);
    }

    job.done = true;
  } catch (error) {
    const msg =
      error instanceof Error ? error.message : "Unknown error occurred";
    console.error("Audit job error:", msg);
    pushJobEvent(jobId, { type: "error", message: msg });
    job.done = true;
    job.error = msg;
  }
}
