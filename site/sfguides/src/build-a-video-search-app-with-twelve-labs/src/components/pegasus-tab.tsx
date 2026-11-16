'use client';

import { AgentTrace } from '@/components/agent-trace';
import { type Attachment, AttachmentDrop } from '@/components/attachment-drop';
import type { VideoItem } from '@/app/api/videos/route';
import { PEGASUS_PRESETS } from '@/lib/constants';
import { formatTs, useAgent } from '@/lib/use-agent';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { ArrowUp, Clapperboard, Film, Loader2, Square, Upload } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface PegasusSeed {
  stage: 'TRAILERS_STAGE' | 'VOYAGERS_STAGE';
  path: string;
  start?: number;
  end?: number;
  prompt: string;
  nonce: number;
}

/** "m:ss" | "h:mm:ss" | seconds -> seconds (NaN if invalid). */
function parseTs(v: string): number {
  const parts = v.trim().split(':').map(Number);
  if (!parts.length || parts.some((p) => !Number.isFinite(p) || p < 0)) return NaN;
  return parts.reduce((acc, p) => acc * 60 + p, 0);
}

const MAX_CLIP_SEC = 600;

type Source = 'TRAILERS_STAGE' | 'VOYAGERS_STAGE' | 'UPLOAD';

/** Pegasus returns free text; render it as JSON when it is JSON (optionally fenced). */
function parseJson(text: string): unknown | null {
  const t = text.trim().replace(/^```(?:json)?\s*/i, '').replace(/```\s*$/, '');
  if (!t.startsWith('{') && !t.startsWith('[')) return null;
  try {
    return JSON.parse(t);
  } catch {
    return null;
  }
}

function JsonView({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (Array.isArray(value)) {
    return (
      <ul className="space-y-1.5">
        {value.map((v, i) => (
          <li key={i} className="rounded-lg bg-muted/40 p-2">
            <JsonView value={v} depth={depth + 1} />
          </li>
        ))}
      </ul>
    );
  }
  if (value && typeof value === 'object') {
    return (
      <dl className={cn('grid gap-x-4 gap-y-1.5', depth === 0 && 'gap-y-3')} style={{ gridTemplateColumns: 'minmax(80px,auto) 1fr' }}>
        {Object.entries(value as Record<string, unknown>).map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="text-xs font-medium uppercase tracking-wider text-pegasus/80">{k.replace(/_/g, ' ')}</dt>
            <dd className="min-w-0 text-sm">
              <JsonView value={v} depth={depth + 1} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }
  return <span className="break-words">{String(value)}</span>;
}

export function PegasusTab({ seed }: { seed: PegasusSeed | null }) {
  const { state, run, stop, reset } = useAgent();
  const [source, setSource] = useState<Source>('TRAILERS_STAGE');
  const [selected, setSelected] = useState<string | null>(null);
  const [upload, setUpload] = useState<Attachment | null>(null);
  const [prompt, setPrompt] = useState(PEGASUS_PRESETS[0].prompt);
  const [rangeStart, setRangeStart] = useState('0:00');
  const [rangeEnd, setRangeEnd] = useState('2:00');
  const running = state.status === 'running';

  const videos = useQuery({
    queryKey: ['videos'],
    queryFn: async () => {
      const r = await fetch('/api/videos');
      const j = await r.json();
      if (!r.ok) throw new Error(j.error);
      return j.items as VideoItem[];
    },
    staleTime: 5 * 60_000,
  });

  const list = useMemo(() => (videos.data ?? []).filter((v) => v.stage === source), [videos.data, source]);

  useEffect(() => {
    if (source !== 'UPLOAD' && list.length && !list.some((v) => v.path === selected)) setSelected(list[0].path);
  }, [list, selected, source]);

  // Handoff from the Marengo tab.
  useEffect(() => {
    if (!seed) return;
    setSource(seed.stage);
    setSelected(seed.path);
    setPrompt(seed.prompt);
    if (seed.start != null) {
      setRangeStart(formatTs(seed.start));
      setRangeEnd(formatTs(seed.end ?? seed.start + 60));
    }
    reset();
  }, [seed, reset]);

  const stage = source === 'UPLOAD' ? 'SEARCH_UPLOADS' : source;
  const file = source === 'UPLOAD' ? (upload?.kind === 'video' ? upload.path : null) : selected;

  const preview = useQuery({
    queryKey: ['clip-url', stage, file],
    enabled: !!file && source !== 'UPLOAD',
    queryFn: async () => {
      const r = await fetch(`/api/clip-url?stage=${stage}&path=${encodeURIComponent(file!)}`);
      const j = await r.json();
      if (!r.ok) throw new Error(j.error);
      return j.url as string;
    },
    staleTime: 50 * 60_000,
  });
  const previewUrl = source === 'UPLOAD' ? upload?.previewUrl : preview.data;

  const needsRange = source === 'VOYAGERS_STAGE';
  const startSec = parseTs(rangeStart);
  const endSec = parseTs(rangeEnd);
  const rangeError = !needsRange
    ? null
    : !Number.isFinite(startSec) || !Number.isFinite(endSec)
      ? 'Use m:ss, e.g. 31:20'
      : endSec <= startSec
        ? 'End must be after start'
        : endSec - startSec > MAX_CLIP_SEC
          ? 'Max 10 minutes per clip'
          : null;

  function submit() {
    if (running || !file || !prompt.trim() || rangeError) return;
    run({
      tab: 'pegasus',
      message: prompt.trim(),
      stage,
      file,
      attachment: source === 'UPLOAD' ? file : null,
      rangeStart: needsRange ? startSec : null,
      rangeEnd: needsRange ? endSec : null,
    });
  }

  const analysis = state.pegasus?.analysis;
  const json = analysis ? parseJson(analysis) : null;

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
      <div className="min-w-0 space-y-5">
        <div className="tl-panel overflow-hidden">
          <div className="relative aspect-video bg-black">
            {previewUrl ? (
              <video
                key={previewUrl}
                src={needsRange && Number.isFinite(startSec) ? `${previewUrl}#t=${startSec}` : previewUrl}
                controls
                playsInline
                className="h-full w-full"
              />
            ) : (
              <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
                {preview.isFetching ? <Loader2 className="h-5 w-5 animate-spin" /> : <Clapperboard className="h-6 w-6 text-pegasus" />}
                {source === 'UPLOAD' ? 'Upload a video for Pegasus to watch' : 'Pick a video'}
              </div>
            )}
          </div>
          <div className="space-y-3 p-4">
            <div className="flex flex-wrap gap-2">
              {(
                [
                  ['TRAILERS_STAGE', 'Trailers', Film],
                  ['VOYAGERS_STAGE', 'Voyagers! episodes', Clapperboard],
                  ['UPLOAD', 'Upload', Upload],
                ] as const
              ).map(([id, label, Icon]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setSource(id)}
                  className={cn(
                    'tl-pill transition-colors',
                    source === id ? 'border-pegasus/60 bg-pegasus/10 text-pegasus' : 'border-border text-muted-foreground hover:text-foreground',
                  )}
                >
                  <Icon className="h-3.5 w-3.5" /> {label}
                </button>
              ))}
            </div>
            {source === 'UPLOAD' ? (
              <AttachmentDrop value={upload} onChange={setUpload} accept="video/*" label="Drop a video (mp4/mov) to analyze" />
            ) : videos.isPending ? (
              <div className="h-10 animate-pulse rounded-lg bg-muted/50" />
            ) : videos.isError ? (
              <p className="text-sm text-destructive">{(videos.error as Error).message}</p>
            ) : (
              <div className="flex max-h-44 flex-wrap gap-2 overflow-y-auto">
                {list.map((v) => (
                  <button
                    key={v.path}
                    type="button"
                    onClick={() => setSelected(v.path)}
                    className={cn(
                      'max-w-full truncate rounded-lg border px-3 py-1.5 text-left text-xs transition-colors',
                      selected === v.path ? 'border-pegasus/60 bg-pegasus/10 text-foreground' : 'text-muted-foreground hover:text-foreground',
                    )}
                    title={v.path}
                  >
                    {v.title}
                  </button>
                ))}
              </div>
            )}
            {needsRange && (
              <div className="flex flex-wrap items-center gap-2 rounded-lg bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
                <span>Clip range</span>
                <input
                  value={rangeStart}
                  onChange={(e) => setRangeStart(e.target.value)}
                  className="w-16 rounded-md border bg-background px-2 py-1 font-mono text-foreground outline-none focus:border-pegasus"
                  aria-label="Clip start"
                />
                <span>–</span>
                <input
                  value={rangeEnd}
                  onChange={(e) => setRangeEnd(e.target.value)}
                  className="w-16 rounded-md border bg-background px-2 py-1 font-mono text-foreground outline-none focus:border-pegasus"
                  aria-label="Clip end"
                />
                <span className={cn('ml-1', rangeError && 'text-destructive')}>
                  {rangeError ?? 'Full episodes are clipped server-side (max 10 min) before Pegasus watches them.'}
                </span>
              </div>
            )}
          </div>
        </div>

        <form
          className="tl-panel space-y-3 p-4"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <div className="flex flex-wrap gap-2">
            {PEGASUS_PRESETS.map((p) => (
              <button
                key={p.label}
                type="button"
                onClick={() => setPrompt(p.prompt)}
                className={cn(
                  'tl-pill transition-colors',
                  prompt === p.prompt ? 'border-pegasus/60 bg-pegasus/10 text-pegasus' : 'border-border text-muted-foreground hover:text-foreground',
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
          <div className="flex items-end gap-3">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={3}
              placeholder="Ask Pegasus anything about this video…"
              className="min-w-0 flex-1 resize-none bg-transparent text-sm leading-relaxed outline-none placeholder:text-muted-foreground"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit();
              }}
            />
            {running ? (
              <button type="button" onClick={stop} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-muted" aria-label="Stop">
                <Square className="h-4 w-4" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!file || !prompt.trim() || !!rangeError}
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-pegasus text-black disabled:opacity-30"
                aria-label="Analyze"
              >
                <ArrowUp className="h-5 w-5" />
              </button>
            )}
          </div>
          <p className="text-xs text-muted-foreground">twelvelabs-pegasus-1-5 via AI_COMPLETE · ⌘↵ to run</p>
        </form>

        {analysis && (
          <section className="tl-panel p-5 animate-in fade-in slide-in-from-bottom-2 motion-reduce:animate-none">
            <h2 className="mb-3 text-xs font-medium uppercase tracking-[0.14em] text-pegasus">Pegasus output</h2>
            {json ? (
              <JsonView value={json} />
            ) : (
              <div className="prose-agent text-sm text-foreground/90">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{analysis}</ReactMarkdown>
              </div>
            )}
          </section>
        )}
      </div>

      <aside className="tl-panel h-fit min-w-0 overflow-y-auto overscroll-contain max-h-[70vh] lg:sticky lg:top-40 lg:max-h-[calc(100vh-11rem)]">
        <AgentTrace state={state} emptyHint="Choose a video and a prompt. The agent briefs Pegasus, then summarizes what it found." />
      </aside>
    </div>
  );
}
