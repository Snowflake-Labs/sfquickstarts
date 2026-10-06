"use client";

import { useState, useCallback, useRef } from "react";
import { pollJob } from "@/hooks/useAudit";
import type { Finding, StreamEvent } from "@/lib/types";

export interface FixMessage {
  role: "user" | "assistant";
  text: string;
}

export interface SuggestFixState {
  activeIndex: number | null;
  loading: boolean;
  messages: FixMessage[];
  error: string | null;
  finding: Finding | null;
}

const IDLE: SuggestFixState = {
  activeIndex: null,
  loading: false,
  messages: [],
  error: null,
  finding: null,
};

export function useSuggestFix() {
  const [state, setState] = useState<SuggestFixState>(IDLE);
  const abortRef = useRef<AbortController | null>(null);

  const requestFix = useCallback(
    async (index: number, finding: Finding, database: string) => {
      // If already loading, ignore (one at a time)
      if (abortRef.current) return;

      const controller = new AbortController();
      abortRef.current = controller;

      setState({
        activeIndex: index,
        loading: true,
        messages: [],
        error: null,
        finding,
      });

      let text = "";

      try {
        const resp = await fetch("/api/suggest-fix", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ finding, database }),
          credentials: "include",
          signal: controller.signal,
        });

        if (!resp.ok) {
          const errorData = await resp.json().catch(() => ({}));
          throw new Error(
            (errorData as Record<string, string>).error ||
              `Server error: ${resp.status}`
          );
        }

        const { jobId } = await resp.json();

        await pollJob(
          jobId,
          (event: StreamEvent) => {
            if (controller.signal.aborted) return;

            if (event.type === "text") {
              text += event.text;
              setState((prev) => ({
                ...prev,
                messages: [{ role: "assistant", text }],
              }));
            } else if (event.type === "error") {
              setState((prev) => ({
                ...prev,
                loading: false,
                error: event.message,
              }));
            } else if (event.type === "result") {
              setState((prev) => ({
                ...prev,
                loading: false,
                messages:
                  prev.messages.length > 0
                    ? prev.messages
                    : text
                      ? [{ role: "assistant", text }]
                      : prev.messages,
              }));
            }
          },
          controller.signal
        );

        // Ensure loading is cleared
        if (!controller.signal.aborted) {
          setState((prev) =>
            prev.loading ? { ...prev, loading: false } : prev
          );
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        const msg = err instanceof Error ? err.message : "Unknown error";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: msg,
        }));
      } finally {
        abortRef.current = null;
      }
    },
    []
  );

  const sendFollowUp = useCallback(
    async (message: string) => {
      if (abortRef.current) return; // Already busy

      const controller = new AbortController();
      abortRef.current = controller;

      // Append user message and set loading
      setState((prev) => ({
        ...prev,
        loading: true,
        error: null,
        messages: [...prev.messages, { role: "user", text: message }],
      }));

      let text = "";

      try {
        const resp = await fetch("/api/suggest-fix/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
          credentials: "include",
          signal: controller.signal,
        });

        if (!resp.ok) {
          const errorData = await resp.json().catch(() => ({}));
          throw new Error(
            (errorData as Record<string, string>).error ||
              `Server error: ${resp.status}`
          );
        }

        const { jobId } = await resp.json();

        await pollJob(
          jobId,
          (event: StreamEvent) => {
            if (controller.signal.aborted) return;

            if (event.type === "text") {
              text += event.text;
              setState((prev) => {
                const msgs = [...prev.messages];
                // Update or append the streaming assistant message
                if (msgs.length > 0 && msgs[msgs.length - 1].role === "assistant" && msgs[msgs.length - 1].text === "") {
                  msgs[msgs.length - 1] = { role: "assistant", text };
                } else if (msgs.length === 0 || msgs[msgs.length - 1].role === "user") {
                  msgs.push({ role: "assistant", text });
                } else {
                  msgs[msgs.length - 1] = { role: "assistant", text };
                }
                return { ...prev, messages: msgs };
              });
            } else if (event.type === "error") {
              setState((prev) => ({
                ...prev,
                loading: false,
                error: event.message,
              }));
            } else if (event.type === "result") {
              setState((prev) => ({
                ...prev,
                loading: false,
              }));
            }
          },
          controller.signal
        );

        if (!controller.signal.aborted) {
          setState((prev) =>
            prev.loading ? { ...prev, loading: false } : prev
          );
        }
      } catch (err) {
        if (controller.signal.aborted) return;
        const msg = err instanceof Error ? err.message : "Unknown error";
        setState((prev) => ({
          ...prev,
          loading: false,
          error: msg,
        }));
      } finally {
        abortRef.current = null;
      }
    },
    []
  );

  const dismissFix = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setState(IDLE);
    // Tell server to close the fix session
    fetch("/api/suggest-fix/dismiss", {
      method: "POST",
      credentials: "include",
    }).catch(() => {});
  }, []);

  return { fixState: state, requestFix, sendFollowUp, dismissFix };
}
