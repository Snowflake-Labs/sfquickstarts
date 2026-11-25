'use client';

import { useCallback, useRef, useState } from 'react';

export interface Clip {
  segment_id: string;
  episode: string;
  start_sec: number;
  end_sec: number;
  video_url: string | null;
  /** Fused score in [0,1] after per-index normalization. */
  score?: number;
  modality_scores?: Record<string, { normalized: number; raw: number; weight: number }>;
}

export interface MarengoPayload {
  query?: string;
  attachment?: string | null;
  modalities?: string[];
  results: Clip[];
}

export interface PegasusPayload {
  stage: string;
  file: string;
  analysis: string;
  start_sec?: number;
  end_sec?: number;
}

export interface ToolStep {
  id: string;
  name: string;
  input?: unknown;
  status: 'running' | 'done' | 'error';
  ms?: number;
}

export interface AgentState {
  status: 'idle' | 'running' | 'done' | 'error';
  statusMessage: string;
  text: string;
  thinking: string;
  steps: ToolStep[];
  marengo: MarengoPayload | null;
  pegasus: PegasusPayload | null;
  error: string | null;
}

export interface AgentRunInput {
  tab: 'marengo' | 'pegasus';
  message: string;
  attachment?: string | null;
  stage?: string | null;
  file?: string | null;
  modalities?: string[];
  rangeStart?: number | null;
  rangeEnd?: number | null;
}

interface HistoryMessage {
  role: 'user' | 'assistant';
  content: { type: 'text'; text: string }[];
}

const INITIAL: AgentState = {
  status: 'idle',
  statusMessage: '',
  text: '',
  thinking: '',
  steps: [],
  marengo: null,
  pegasus: null,
  error: null,
};

/** Walk a tool result looking for the MARENGO_SEARCH / PEGASUS_ANALYZE payload shapes. */
function findPayload(value: unknown, depth = 0): MarengoPayload | PegasusPayload | null {
  if (depth > 6 || value == null) return null;
  if (typeof value === 'string') {
    const s = value.trim();
    if (s.startsWith('{') || s.startsWith('[')) {
      try {
        return findPayload(JSON.parse(s), depth + 1);
      } catch {
        return null;
      }
    }
    return null;
  }
  if (Array.isArray(value)) {
    for (const v of value) {
      const hit = findPayload(v, depth + 1);
      if (hit) return hit;
    }
    return null;
  }
  if (typeof value === 'object') {
    const o = value as Record<string, unknown>;
    if (Array.isArray(o.results) && o.results.every((r) => r && typeof r === 'object' && 'episode' in (r as object))) {
      return o as unknown as MarengoPayload;
    }
    if (typeof o.analysis === 'string' && typeof o.file === 'string') return o as unknown as PegasusPayload;
    for (const v of Object.values(o)) {
      const hit = findPayload(v, depth + 1);
      if (hit) return hit;
    }
  }
  return null;
}

/** Split an SSE buffer into complete events; returns leftover partial text. */
function parseSse(buffer: string): { events: { event: string; data: string }[]; rest: string } {
  const events: { event: string; data: string }[] = [];
  const chunks = buffer.split(/\r?\n\r?\n/);
  const rest = chunks.pop() ?? '';
  for (const chunk of chunks) {
    let event = 'message';
    const data: string[] = [];
    for (const line of chunk.split(/\r?\n/)) {
      if (line.startsWith('event:')) event = line.slice(6).trim();
      else if (line.startsWith('data:')) data.push(line.slice(5).replace(/^ /, ''));
    }
    if (data.length) events.push({ event, data: data.join('\n') });
  }
  return { events, rest };
}

/** Streams a Cortex Agent run through /api/agent and keeps a short conversation history per tab. */
export function useAgent() {
  const [state, setState] = useState<AgentState>(INITIAL);
  const history = useRef<HistoryMessage[]>([]);
  const abort = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abort.current?.abort();
    history.current = [];
    setState(INITIAL);
  }, []);

  const stop = useCallback(() => abort.current?.abort(), []);

  const run = useCallback(async (input: AgentRunInput) => {
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    setState({ ...INITIAL, status: 'running', statusMessage: 'Planning…' });

    const started: Record<string, number> = {};
    let finalText = '';

    try {
      const res = await fetch('/api/agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...input, history: history.current }),
        signal: controller.signal,
      });
      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || `Request failed (${res.status})`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const { events, rest } = parseSse(buffer);
        buffer = rest;
        for (const { event, data } of events) {
          let d: Record<string, any> = {};
          try {
            d = JSON.parse(data);
          } catch {
            continue;
          }
          switch (event) {
            case 'response.status':
              setState((s) => ({ ...s, statusMessage: d.message ?? s.statusMessage }));
              break;
            case 'response.thinking.delta':
              setState((s) => ({ ...s, thinking: s.thinking + (d.text ?? '') }));
              break;
            case 'response.text.delta':
              finalText += d.text ?? '';
              setState((s) => ({ ...s, text: s.text + (d.text ?? '') }));
              break;
            case 'response.tool_use': {
              const id = d.tool_use_id ?? `${d.name}-${Date.now()}`;
              started[id] = performance.now();
              setState((s) => ({
                ...s,
                statusMessage: `Running ${d.name}…`,
                steps: [...s.steps, { id, name: d.name, input: d.input, status: 'running' }],
              }));
              break;
            }
            case 'response.tool_result': {
              const id = d.tool_use_id;
              const payload = findPayload(d.content);
              const ok = d.status !== 'error';
              setState((s) => ({
                ...s,
                steps: s.steps.map((st) =>
                  st.id === id
                    ? { ...st, status: ok ? 'done' : 'error', ms: started[id] ? performance.now() - started[id] : undefined }
                    : st,
                ),
                marengo: payload && 'results' in payload ? payload : s.marengo,
                pegasus: payload && 'analysis' in payload ? payload : s.pegasus,
              }));
              break;
            }
            case 'response':
              // Final aggregated message; use its text if we missed deltas.
              if (!finalText && Array.isArray(d.content)) {
                const t = d.content.filter((c: any) => c.type === 'text').map((c: any) => c.text).join('\n');
                finalText = t;
                setState((s) => ({ ...s, text: t }));
              }
              break;
            case 'error':
              throw new Error(d.message ?? 'Agent error');
          }
        }
      }

      history.current = [
        ...history.current,
        { role: 'user', content: [{ type: 'text', text: input.message }] },
        { role: 'assistant', content: [{ type: 'text', text: finalText || '(no text response)' }] },
      ].slice(-8) as HistoryMessage[];
      setState((s) => ({ ...s, status: 'done', statusMessage: '' }));
    } catch (e) {
      if (controller.signal.aborted) {
        setState((s) => ({ ...s, status: 'idle', statusMessage: '' }));
        return;
      }
      setState((s) => ({ ...s, status: 'error', error: e instanceof Error ? e.message : String(e) }));
    }
  }, []);

  return { state, run, stop, reset };
}

/** Upload one image/video to SEARCH_UPLOADS via /api/upload. */
export async function uploadAttachment(file: File): Promise<{ path: string; kind: 'image' | 'video' }> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/upload', { method: 'POST', body: form });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error ?? 'Upload failed');
  return json;
}

export function formatTs(sec: number): string {
  const s = Math.max(0, Math.floor(sec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}` : `${m}:${String(r).padStart(2, '0')}`;
}
