import { NextRequest, NextResponse } from "next/server";
import { createAgentClient } from "@/lib/agent-client";
import { jobStore, pushJobEvent } from "@/lib/audit-store";
import {
  getFixSession,
  setFixSession,
  isFixActive,
  setFixActive,
} from "@/app/api/suggest-fix/route";

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

  const fixThread = getFixSession();
  if (!fixThread) {
    return NextResponse.json(
      { error: "No active fix session. Request a fix first." },
      { status: 400 },
    );
  }

  if (isFixActive()) {
    return NextResponse.json(
      { error: "A fix response is still generating." },
      { status: 409 },
    );
  }

  setFixActive(true);
  const jobId = `fixchat-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  jobStore.set(jobId, { events: [], done: false });

  const response = NextResponse.json({ jobId });

  runFixChatJob(jobId, message)
    .catch((err) => {
      console.error("Fix chat job error:", err);
    })
    .finally(() => {
      setFixActive(false);
    });

  return response;
}

async function runFixChatJob(jobId: string, message: string) {
  const job = jobStore.get(jobId);
  const fixThread = getFixSession();
  if (!job || !fixThread) {
    if (job) {
      pushJobEvent(jobId, {
        type: "error",
        message: "No active fix session.",
      });
      job.done = true;
    }
    return;
  }

  try {
    const client = createAgentClient();

    // Append user message to the thread
    fixThread.push({
      role: "user",
      content: [{ type: "text", text: message }],
    });

    const stream = client.codingAgent.stream({
      permissionPolicy: "always_allow",
      messages: fixThread,
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

    // Append assistant response to thread
    if (accumulatedText) {
      fixThread.push({
        role: "assistant",
        content: [{ type: "text", text: accumulatedText }],
      });
      setFixSession(fixThread);
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
    console.error("Fix chat error:", msg);
    pushJobEvent(jobId, { type: "error", message: msg });
    job.done = true;
    job.error = msg;
  }
}
