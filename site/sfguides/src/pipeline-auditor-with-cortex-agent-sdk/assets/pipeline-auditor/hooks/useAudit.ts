"use client";

import { useState, useCallback, useRef } from "react";
import type {
  AuditReport,
  ChatMessage,
  StreamEvent,
  ToolProgressEvent,
} from "@/lib/types";

interface AuditState {
  isAuditing: boolean;
  isLoading: boolean;
  report: AuditReport | null;
  messages: ChatMessage[];
  toolProgress: ToolProgressEvent[];
  error: string | null;
  stats: {
    durationMs: number;
    numTurns: number;
    toolCalls: number;
  } | null;
}

const POLL_INTERVAL_MS = 2000;

// Poll a job for events until done or aborted (retries on 5xx)
const MAX_POLL_RETRIES = 3;
const RETRY_BACKOFF_MS = [2000, 4000, 8000];

export async function pollJob(
  jobId: string,
  onEvent: (event: StreamEvent) => void,
  signal: AbortSignal
): Promise<void> {
  let cursor = 0;
  let retries = 0;
  while (!signal.aborted) {
    const resp = await fetch(`/api/audit/progress?jobId=${encodeURIComponent(jobId)}&after=${cursor}`, {
      credentials: "include",
      signal,
    });
    if (!resp.ok) {
      // Retry on 5xx (transient proxy/server errors)
      if (resp.status >= 500 && retries < MAX_POLL_RETRIES) {
        const delay = RETRY_BACKOFF_MS[retries] || 8000;
        retries++;
        await new Promise<void>((resolve, reject) => {
          const timer = setTimeout(resolve, delay);
          signal.addEventListener("abort", () => {
            clearTimeout(timer);
            reject(new DOMException("Aborted", "AbortError"));
          }, { once: true });
        });
        continue;
      }
      throw new Error(`Poll error: ${resp.status}`);
    }
    retries = 0; // Reset on success
    const data = await resp.json();
    for (const event of data.events as StreamEvent[]) {
      if (signal.aborted) return;
      onEvent(event);
    }
    cursor = data.cursor;
    if (data.done) return;
    // Wait before next poll
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(resolve, POLL_INTERVAL_MS);
      signal.addEventListener("abort", () => {
        clearTimeout(timer);
        reject(new DOMException("Aborted", "AbortError"));
      }, { once: true });
    });
  }
}

export function useAudit() {
  const [state, setState] = useState<AuditState>({
    isAuditing: false,
    isLoading: false,
    report: null,
    messages: [],
    toolProgress: [],
    error: null,
    stats: null,
  });

  const abortRef = useRef<AbortController | null>(null);

  // Start a new audit
  const startAudit = useCallback(
    async (database: string, scope: string[] = [], schema: string = "") => {
      // Abort any existing request
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const assistantMsgId = `audit-${Date.now()}`;
      let assistantText = "";
      const thinkingSteps: string[] = [];
      const toolCalls: ToolProgressEvent[] = [];

      setState({
        isAuditing: true,
        isLoading: true,
        report: null,
        messages: [
          {
            id: `user-${Date.now()}`,
            role: "user",
            text: schema
              ? `Audit ${database} database, schema ${schema}, scope ${scope.join("|")}`
              : `Audit ${database} database, scope ${scope.join("|")}`,
            timestamp: new Date(),
          },
          {
            id: assistantMsgId,
            role: "assistant",
            text: "",
            timestamp: new Date(),
            isStreaming: true,
            thinkingSteps: [],
            toolCalls: [],
          },
        ],
        toolProgress: [],
        error: null,
        stats: null,
      });

      try {
        // Start the audit — server returns jobId immediately
        const startResp = await fetch("/api/audit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ database, scope, schema }),
          signal: controller.signal,
          credentials: "include",
        });

        if (!startResp.ok) {
          throw new Error(`Server error: ${startResp.status}`);
        }

        const { jobId } = await startResp.json();

        // Poll for events
        await pollJob(jobId, (event) => {
          if (controller.signal.aborted) return;

          switch (event.type) {
            case "status":
              break;

            case "tool_progress":
              toolCalls.push(event);
              setState((prev) => ({
                ...prev,
                toolProgress: [...toolCalls],
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        toolCalls: toolCalls.map((tc) => ({
                          toolName: tc.toolName,
                          elapsed: tc.elapsed,
                          sqlPreview: tc.sqlPreview,
                          description: tc.description,
                        })),
                      }
                    : m
                ),
              }));
              break;

            case "thinking":
              thinkingSteps.push(event.text);
              setState((prev) => ({
                ...prev,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, thinkingSteps: [...thinkingSteps] }
                    : m
                ),
              }));
              break;

            case "text":
              assistantText += event.text;
              setState((prev) => ({
                ...prev,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, text: assistantText }
                    : m
                ),
              }));
              break;

            case "report":
              setState((prev) => ({
                ...prev,
                report: event.report,
              }));
              break;

            case "result":
              if (event.report) {
                setState((prev) => ({
                  ...prev,
                  report: prev.report || event.report || null,
                }));
              }
              setState((prev) => ({
                ...prev,
                isLoading: false,
                stats: {
                  durationMs: event.durationMs,
                  numTurns: event.numTurns,
                  toolCalls: event.toolCalls || toolCalls.length,
                },
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, isStreaming: false }
                    : m
                ),
              }));
              break;

            case "error":
              setState((prev) => ({
                ...prev,
                isLoading: false,
                error: event.message,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        isStreaming: false,
                        text: `Error: ${event.message}`,
                      }
                    : m
                ),
              }));
              break;
          }
        }, controller.signal);

        // Polling finished (job done) — ensure final state
        if (!controller.signal.aborted) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            messages: prev.messages.map((m) =>
              m.id === assistantMsgId ? { ...m, isStreaming: false } : m
            ),
          }));
        }
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }
        const msg = err instanceof Error ? err.message : "Unknown error";
        setState((prev) => ({
          ...prev,
          isLoading: false,
          isAuditing: false,
          error: msg,
        }));
      }
    },
    []
  );

  // Send a follow-up chat message
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || state.isLoading) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        role: "user",
        text: text.trim(),
        timestamp: new Date(),
      };

      const assistantMsgId = `chat-${Date.now()}`;
      let assistantText = "";
      const thinkingSteps: string[] = [];

      setState((prev) => ({
        ...prev,
        isLoading: true,
        messages: [
          ...prev.messages,
          userMsg,
          {
            id: assistantMsgId,
            role: "assistant",
            text: "",
            timestamp: new Date(),
            isStreaming: true,
            thinkingSteps: [],
            toolCalls: [],
          },
        ],
      }));

      try {
        const startResp = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text.trim() }),
          credentials: "include",
        });

        if (!startResp.ok) {
          const errorData = await startResp.json().catch(() => ({}));
          throw new Error(
            (errorData as Record<string, string>).error ||
              `Server error: ${startResp.status}`
          );
        }

        const { jobId } = await startResp.json();
        const controller = new AbortController();

        await pollJob(jobId, (event) => {
          switch (event.type) {
            case "text":
              assistantText += event.text;
              setState((prev) => ({
                ...prev,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, text: assistantText }
                    : m
                ),
              }));
              break;

            case "thinking":
              thinkingSteps.push(event.text);
              setState((prev) => ({
                ...prev,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, thinkingSteps: [...thinkingSteps] }
                    : m
                ),
              }));
              break;

            case "tool_use":
              setState((prev) => ({
                ...prev,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        toolCalls: [
                          ...(m.toolCalls || []),
                          { toolName: event.toolName },
                        ],
                      }
                    : m
                ),
              }));
              break;

            case "result":
              setState((prev) => ({
                ...prev,
                isLoading: false,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, isStreaming: false }
                    : m
                ),
              }));
              break;

            case "error":
              setState((prev) => ({
                ...prev,
                isLoading: false,
                messages: prev.messages.map((m) =>
                  m.id === assistantMsgId
                    ? {
                        ...m,
                        isStreaming: false,
                        text: `Error: ${event.message}`,
                      }
                    : m
                ),
              }));
              break;
          }
        }, controller.signal);

        setState((prev) => ({
          ...prev,
          isLoading: false,
          messages: prev.messages.map((m) =>
            m.id === assistantMsgId ? { ...m, isStreaming: false } : m
          ),
        }));
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setState((prev) => ({
          ...prev,
          isLoading: false,
          messages: prev.messages.map((m) =>
            m.id === assistantMsgId
              ? { ...m, isStreaming: false, text: `Error: ${msg}` }
              : m
          ),
        }));
      }
    },
    [state.isLoading]
  );

  const cancelAudit = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
      // Full reset — return to landing page
      setState({
        isAuditing: false,
        isLoading: false,
        report: null,
        messages: [],
        toolProgress: [],
        error: null,
        stats: null,
      });
    }
  }, []);

  // Reset view to landing page (works even after audit is complete)
  const resetView = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setState({
      isAuditing: false,
      isLoading: false,
      report: null,
      messages: [],
      toolProgress: [],
      error: null,
      stats: null,
    });
  }, []);

  return {
    ...state,
    startAudit,
    sendMessage,
    cancelAudit,
    resetView,
  };
}
