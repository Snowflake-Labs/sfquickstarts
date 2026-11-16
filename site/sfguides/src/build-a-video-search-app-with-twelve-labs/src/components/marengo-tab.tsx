'use client';

import { AgentTrace } from '@/components/agent-trace';
import { type Attachment, AttachmentDrop } from '@/components/attachment-drop';
import { ClipCard } from '@/components/clip-card';
import { type Clip, useAgent } from '@/lib/use-agent';
import { ArrowUp, Loader2, Search, Square } from 'lucide-react';
import { useState } from 'react';

export function MarengoTab({ onAskPegasus }: { onAskPegasus: (clip: Clip) => void }) {
  const { state, run, stop } = useAgent();
  const [query, setQuery] = useState('');
  const [attachment, setAttachment] = useState<Attachment | null>(null);
  const running = state.status === 'running';
  const clips = state.marengo?.results ?? [];

  function submit(text = query) {
    if (running || (!text.trim() && !attachment)) return;
    run({ tab: 'marengo', message: text.trim(), attachment: attachment?.path ?? null });
  }

  return (
    <div className="space-y-6">
      <form
        className="tl-panel space-y-4 p-4 sm:p-5"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <div className="flex items-center gap-3">
          <Search className="h-5 w-5 shrink-0 text-marengo" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={attachment ? 'Optional: describe what to match in your attachment…' : 'Describe a moment — what you see, hear, or what is said…'}
            className="min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground sm:text-lg"
          />
          {running ? (
            <button
              type="button"
              onClick={stop}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted text-foreground"
              aria-label="Stop"
            >
              <Square className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!query.trim() && !attachment}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-marengo text-black transition-opacity disabled:opacity-30"
              aria-label="Search"
            >
              <ArrowUp className="h-5 w-5" />
            </button>
          )}
        </div>

        <AttachmentDrop
          value={attachment}
          onChange={setAttachment}
          compact
          label="Search by example — drop an image or a short video clip"
        />

        <p className="text-xs text-muted-foreground">
          Searches visual, speech and audio together · Cortex Search multi-index · twelvelabs-marengo-embed-3-0
        </p>
      </form>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <section className="min-w-0">
          {running && !clips.length ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="tl-panel aspect-[4/3] animate-pulse bg-muted/40" />
              ))}
            </div>
          ) : clips.length ? (
            <>
              <div className="mb-3 flex items-baseline gap-2">
                <h2 className="text-sm font-medium">Moments</h2>
                <span className="text-xs text-muted-foreground">{clips.length} clips · diversified across videos</span>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {clips.map((c, i) => (
                  <ClipCard key={c.segment_id} clip={c} rank={i} onAskPegasus={onAskPegasus} />
                ))}
              </div>
            </>
          ) : state.status === 'done' ? (
            <div className="tl-panel flex min-h-48 items-center justify-center p-6 text-sm text-muted-foreground">
              The agent answered without running a moment search — try describing something visual.
            </div>
          ) : (
            <div className="tl-panel flex min-h-48 flex-col items-center justify-center gap-2 p-6 text-center text-sm text-muted-foreground">
              {running ? <Loader2 className="h-5 w-5 animate-spin" /> : <Search className="h-5 w-5 text-marengo" />}
              <p className="max-w-sm">
                Marengo embeds every few seconds of video across visual, speech and audio. Search every video
                on your stage by words or by example.
              </p>
            </div>
          )}
        </section>
        <aside className="tl-panel h-fit min-w-0 overflow-y-auto overscroll-contain max-h-[70vh] lg:sticky lg:top-40 lg:max-h-[calc(100vh-11rem)]">
          <AgentTrace state={state} emptyHint="The agent picks the right tool — Marengo search, scene text, or analytics — and explains the hits." />
        </aside>
      </div>
    </div>
  );
}
