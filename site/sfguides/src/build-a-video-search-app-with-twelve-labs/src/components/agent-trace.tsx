'use client';

import type { AgentState } from '@/lib/use-agent';
import { cn } from '@/lib/utils';
import { AlertTriangle, Bot, Brain, CheckCircle2, ChevronDown, Loader2, Wrench } from 'lucide-react';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const TOOL_LABEL: Record<string, string> = {
  MarengoSearch: 'Marengo · multi-index search',
  PegasusAnalyze: 'Pegasus · video understanding',
  VideoAnalyst: 'Cortex Analyst · semantic view',
  SceneSearch: 'Cortex Search · scene text',
};

/** Shows the Cortex Agent's plan (tool calls), status and streamed markdown answer. */
export function AgentTrace({ state, emptyHint }: { state: AgentState; emptyHint: string }) {
  const [showThinking, setShowThinking] = useState(false);
  const running = state.status === 'running';

  if (state.status === 'idle' && !state.text) {
    return (
      <div className="flex h-full min-h-40 flex-col items-center justify-center gap-2 p-6 text-center text-sm text-muted-foreground">
        <Bot className="h-6 w-6 text-tab" />
        <p className="max-w-xs">{emptyHint}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 p-5">
      <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
        <Bot className="h-3.5 w-3.5 text-tab" />
        Cortex Agent
        {running && (
          <span className="ml-auto flex items-center gap-1.5 normal-case tracking-normal">
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            {state.statusMessage || 'Working…'}
          </span>
        )}
      </div>

      {state.steps.length > 0 && (
        <ol className="space-y-1.5">
          {state.steps.map((s) => (
            <li key={s.id} className="flex items-center gap-2 rounded-lg bg-muted/50 px-3 py-2 text-sm">
              {s.status === 'running' ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-tab" />
              ) : s.status === 'done' ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-success" />
              ) : (
                <AlertTriangle className="h-3.5 w-3.5 text-destructive" />
              )}
              <Wrench className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="min-w-0 truncate">{TOOL_LABEL[s.name] ?? s.name}</span>
              {s.ms != null && (
                <span className="ml-auto shrink-0 font-mono text-xs text-muted-foreground">{(s.ms / 1000).toFixed(1)}s</span>
              )}
            </li>
          ))}
        </ol>
      )}

      {state.thinking && (
        <div>
          <button
            type="button"
            onClick={() => setShowThinking((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <Brain className="h-3.5 w-3.5" /> Reasoning
            <ChevronDown className={cn('h-3.5 w-3.5 transition-transform', showThinking && 'rotate-180')} />
          </button>
          {showThinking && (
            <p className="mt-2 whitespace-pre-wrap border-l-2 pl-3 text-xs leading-relaxed text-muted-foreground">
              {state.thinking}
            </p>
          )}
        </div>
      )}

      {state.text && (
        <div className="prose-agent text-sm text-foreground/90">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{state.text}</ReactMarkdown>
        </div>
      )}

      {state.error && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <span className="min-w-0 break-words">{state.error}</span>
        </div>
      )}
    </div>
  );
}
