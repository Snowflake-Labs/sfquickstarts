'use client';

import { type Clip, formatTs } from '@/lib/use-agent';
import { Sparkles } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

const MODALITY_LABEL: Record<string, string> = { visual: 'Visual', transcript: 'Speech', audio: 'Audio' };

/** One Marengo hit: plays the source video from the matched timestamp, with per-index score bars. */
export function ClipCard({ clip, rank, onAskPegasus }: { clip: Clip; rank: number; onAskPegasus: (c: Clip) => void }) {
  const ref = useRef<HTMLVideoElement>(null);
  const [hover, setHover] = useState(false);
  const cols = clip.modality_scores ?? {};
  const total = clip.score;
  const title = clip.episode.replace(/_/g, ' ');

  // Media-fragment URLs aren't honored everywhere; seek explicitly once metadata loads.
  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    const seek = () => {
      v.currentTime = clip.start_sec;
    };
    v.addEventListener('loadedmetadata', seek);
    return () => v.removeEventListener('loadedmetadata', seek);
  }, [clip.start_sec]);

  useEffect(() => {
    const v = ref.current;
    if (!v) return;
    const loop = () => {
      if (v.currentTime > clip.end_sec + 4) v.currentTime = clip.start_sec;
    };
    v.addEventListener('timeupdate', loop);
    return () => v.removeEventListener('timeupdate', loop);
  }, [clip.start_sec, clip.end_sec]);

  return (
    <article
      className="group tl-panel min-w-0 overflow-hidden transition-colors hover:border-[color:var(--accent-tab)]/50 animate-in fade-in slide-in-from-bottom-2 motion-reduce:animate-none"
      style={{ animationDelay: `${rank * 40}ms`, animationFillMode: 'both' }}
      onMouseEnter={() => {
        setHover(true);
        ref.current?.play().catch(() => {});
      }}
      onMouseLeave={() => {
        setHover(false);
        ref.current?.pause();
      }}
    >
      <div className="relative aspect-video bg-black">
        {clip.video_url ? (
          <video
            ref={ref}
            src={`${clip.video_url}#t=${clip.start_sec}`}
            muted={!hover}
            playsInline
            preload="metadata"
            controls={hover}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-xs text-muted-foreground">Preview unavailable</div>
        )}
        <span className="absolute left-2 top-2 rounded-full bg-black/70 px-2 py-0.5 font-mono text-[11px] text-white">
          #{rank + 1}
        </span>
        <span className="absolute right-2 top-2 rounded-full bg-black/70 px-2 py-0.5 font-mono text-[11px] text-[color:var(--marengo)]">
          {formatTs(clip.start_sec)} – {formatTs(clip.end_sec)}
        </span>
      </div>
      <div className="space-y-3 p-4">
        <div className="flex items-start gap-2">
          <h3 className="min-w-0 flex-1 truncate text-sm font-medium" title={clip.episode}>
            {title}
          </h3>
          {total != null && (
            <span className="shrink-0 font-mono text-xs text-muted-foreground" title="Fused score (per-index normalized)">
              {Math.round(total * 100)}
            </span>
          )}
        </div>
        {Object.keys(cols).length > 0 && (
          <div className="space-y-1.5">
            {Object.entries(cols).map(([m, v]) => (
              <div
                key={m}
                className="flex items-center gap-2 text-[11px] text-muted-foreground"
                title={`raw cosine ${v.raw.toFixed(3)} · weight ${v.weight}`}
              >
                <span className="w-12 shrink-0">{MODALITY_LABEL[m] ?? m}</span>
                <div className="h-1 flex-1 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-[color:var(--marengo)]"
                    style={{ width: `${Math.max(3, v.normalized * 100)}%` }}
                  />
                </div>
                <span className="w-9 shrink-0 text-right font-mono">{Math.round(v.normalized * 100)}</span>
              </div>
            ))}
          </div>
        )}
        <button
          type="button"
          onClick={() => onAskPegasus(clip)}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-[color:var(--pegasus)]/30 py-1.5 text-xs font-medium text-[color:var(--pegasus)] transition-colors hover:bg-[color:var(--pegasus)]/10"
        >
          <Sparkles className="h-3.5 w-3.5" /> Ask Pegasus about this moment
        </button>
      </div>
    </article>
  );
}
