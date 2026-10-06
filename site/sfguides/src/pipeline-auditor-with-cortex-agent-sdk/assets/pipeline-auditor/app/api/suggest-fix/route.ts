import { NextRequest, NextResponse } from "next/server";
import { createAgentClient } from "@/lib/agent-client";
import { jobStore, pushJobEvent } from "@/lib/audit-store";

export const dynamic = "force-dynamic";

// Global fix session state: thread messages and lock
const g = globalThis as Record<string, unknown>;
if (!g.__fixSessionMessages) {
  g.__fixSessionMessages = null as Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }> | null;
}
if (!g.__fixJobActive) {
  g.__fixJobActive = false;
}

export function getFixSession(): Array<{
  role: string;
  content: Array<{ type: string; text: string }>;
}> | null {
  return g.__fixSessionMessages as Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }> | null;
}

export function setFixSession(
  messages: Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }> | null,
) {
  g.__fixSessionMessages = messages;
}

export function isFixActive(): boolean {
  return g.__fixJobActive as boolean;
}

export function setFixActive(active: boolean) {
  g.__fixJobActive = active;
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const { finding, database } = body as {
    finding?: Record<string, unknown>;
    database?: string;
  };

  if (!finding || !database) {
    return NextResponse.json(
      { error: "finding and database are required" },
      { status: 400 },
    );
  }

  if (isFixActive()) {
    return NextResponse.json(
      {
        error:
          "A fix is already in progress. Wait for it to finish or dismiss it.",
      },
      { status: 409 },
    );
  }

  setFixActive(true);

  const jobId = `fix-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  jobStore.set(jobId, { events: [], done: false });

  // Close any previous fix session
  setFixSession(null);

  const response = NextResponse.json({ jobId });

  runSuggestFixJob(jobId, finding, database)
    .catch((err) => {
      console.error("Suggest fix job error:", err);
    })
    .finally(() => {
      setFixActive(false);
    });

  return response;
}

async function runSuggestFixJob(
  jobId: string,
  finding: Record<string, unknown>,
  database: string,
) {
  const job = jobStore.get(jobId);
  if (!job) return;

  const systemPrompt = `You are a Snowflake pipeline remediation expert. When given a finding, respond with a clear, actionable fix. Use SQL code blocks for any commands. Give the answer directly from your expertise. If the user asks you to run SQL, you may use sql_execute to run it against Snowflake. Target database: ${database}.`;

  const userPrompt = `Suggest a concrete fix for this pipeline audit finding on the ${database} database.

Finding:
- Severity: ${finding.severity}
- Category: ${finding.category}
- Object: ${finding.object}
- Message: ${finding.message}${finding.details ? `\n- Details: ${JSON.stringify(finding.details)}` : ""}

Rules:
- Do NOT run any tools or queries. Respond with your answer directly.
- Provide exact SQL commands in fenced code blocks where applicable.
- Explain briefly why the fix works.
- Keep the response under 500 words.`;

  const messages: Array<{
    role: string;
    content: Array<{ type: string; text: string }>;
  }> = [
    {
      role: "user",
      content: [
        {
          type: "text",
          text: systemPrompt + "\n\n" + userPrompt,
        },
      ],
    },
  ];

  try {
    const client = createAgentClient();

    const stream = client.codingAgent.stream({
      permissionPolicy: "always_allow",
      messages,
    });

    let accumulatedText = "";

    for await (const event of stream) {
      const ev = event as Record<string, unknown>;

      if (ev.delta) {
        const delta = ev.delta as Record<string, unknown>;
        if (delta.content && Array.isArray(delta.content)) {
          for (const item of delta.content) {
            const block = item as Record<string, unknown>;

            if (block.type === "text" && block.text) {
              accumulatedText += String(block.text);
              pushJobEvent(jobId, {
                type: "text",
                text: String(block.text),
              });
            }
          }
        }
      }
    }

    // Store the conversation thread for follow-up chat
    const thread = [...messages];
    if (accumulatedText) {
      thread.push({
        role: "assistant",
        content: [{ type: "text", text: accumulatedText }],
      });
    }
    setFixSession(thread);

    pushJobEvent(jobId, {
      type: "result",
      isError: false,
      numTurns: 0,
      durationMs: 0,
    });

    job.done = true;
  } catch (error) {
    const msg =
      error instanceof Error ? error.message : "Unknown error occurred";
    console.error("Suggest-fix error:", msg);
    pushJobEvent(jobId, { type: "error", message: msg });
    job.done = true;
    job.error = msg;
  }
}
