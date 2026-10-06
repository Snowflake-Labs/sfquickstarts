import { NextRequest, NextResponse } from "next/server";
import { createAgentClient } from "@/lib/agent-client";
import { jobStore, pushJobEvent } from "@/lib/audit-store";
import { getAuditThread, setAuditThread } from "@/app/api/audit/route";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  const { message } = body as { message?: string };

  if (!message || typeof message !== "string") {
    return NextResponse.json(
      { error: "message is required" },
      { status: 400 },
    );
  }

  const thread = getAuditThread();
  if (thread.length === 0) {
    return NextResponse.json(
      { error: "No active audit session. Run an audit first." },
      { status: 400 },
    );
  }

  const jobId = `chat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  jobStore.set(jobId, { events: [], done: false });

  const response = NextResponse.json({ jobId });

  runChatJob(jobId, message).catch((err) => {
    console.error("Chat job error:", err);
  });

  return response;
}

async function runChatJob(jobId: string, message: string) {
  const job = jobStore.get(jobId);
  if (!job) return;

  const thread = getAuditThread();
  if (thread.length === 0) {
    pushJobEvent(jobId, {
      type: "error",
      message: "No active audit session.",
    });
    job.done = true;
    return;
  }

  try {
    const client = createAgentClient();

    // Append the user message to the thread
    thread.push({
      role: "user",
      content: [{ type: "text", text: message }],
    });

    const stream = client.codingAgent.stream({
      permissionPolicy: "always_allow",
      messages: thread,
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
            } else if (block.type === "tool_use") {
              pushJobEvent(jobId, {
                type: "tool_use",
                toolName: String(block.name || "unknown"),
                toolId: String(block.id || ""),
                input: (block.input as Record<string, unknown>) || {},
              });
            } else if (block.type === "thinking") {
              pushJobEvent(jobId, {
                type: "thinking",
                text: String(block.thinking || block.text || ""),
              });
            }
          }
        }
      }
    }

    // Store assistant response in thread for future follow-ups
    if (accumulatedText) {
      thread.push({
        role: "assistant",
        content: [{ type: "text", text: accumulatedText }],
      });
      setAuditThread(thread);
    }

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
    console.error("Chat error:", msg);
    pushJobEvent(jobId, { type: "error", message: msg });
    job.done = true;
    job.error = msg;
  }
}
