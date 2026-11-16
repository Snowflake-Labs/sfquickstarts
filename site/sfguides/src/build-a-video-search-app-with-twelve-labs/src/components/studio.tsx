'use client';

import { MarengoTab } from '@/components/marengo-tab';
import { type PegasusSeed, PegasusTab } from '@/components/pegasus-tab';
import type { Clip } from '@/lib/use-agent';
import { cn } from '@/lib/utils';
import { useRouter, useSearchParams } from 'next/navigation';
import { useState } from 'react';

type Tab = 'marengo' | 'pegasus';

const TABS: { id: Tab; name: string; kicker: string; headline: string; blurb: string }[] = [
  {
    id: 'marengo',
    name: 'Marengo',
    kicker: 'Embed · Search',
    headline: 'Find any moment.',
    blurb: 'Multimodal search across visual, speech and audio — by words or by example image or clip.',
  },
  {
    id: 'pegasus',
    name: 'Pegasus',
    kicker: 'Generate · Understand',
    headline: 'Ask any video.',
    blurb: 'Summaries, chapters, highlights, brand safety and structured JSON — straight from the pixels.',
  },
];

export function Studio() {
  const params = useSearchParams();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>(params.get('tab') === 'pegasus' ? 'pegasus' : 'marengo');
  const [seed, setSeed] = useState<PegasusSeed | null>(null);
  const active = TABS.find((t) => t.id === tab)!;

  function go(next: Tab) {
    setTab(next);
    router.replace(`/?tab=${next}`, { scroll: false });
  }

  function askPegasus(clip: Clip) {
    setSeed({
      stage: 'VOYAGERS_STAGE',
      path: `${clip.episode}.mp4`,
      start: Math.max(0, clip.start_sec - 15),
      end: clip.end_sec + 45,
      prompt: `Describe exactly what happens in this clip: who is on screen, what they do and say, the setting and the mood. Note the key moments with mm:ss timestamps.`,
      nonce: Date.now(),
    });
    go('pegasus');
  }

  return (
    <div data-tab={tab} className="relative">
      <div className="tl-glow pointer-events-none absolute inset-x-0 top-0 h-[520px]" />
      <main className="relative mx-auto w-full max-w-7xl space-y-8 px-4 pb-16 pt-10 sm:px-6 sm:pt-14 lg:px-8">
        <section className="space-y-5">
          <span className="tl-pill border-border text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-tab" />
            {active.kicker} · Twelve Labs on Snowflake Cortex
          </span>
          <h1 className="text-4xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            {active.headline} <span className="tl-gradient-text whitespace-nowrap">See the unseen.</span>
          </h1>
          <p className="max-w-2xl text-base text-muted-foreground sm:text-lg">{active.blurb}</p>
        </section>

        <div role="tablist" aria-label="Model" className="inline-flex rounded-full border bg-card/60 p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => go(t.id)}
              className={cn(
                'flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium transition-colors',
                tab === t.id
                  ? t.id === 'marengo'
                    ? 'bg-marengo text-black'
                    : 'bg-pegasus text-black'
                  : 'text-muted-foreground hover:text-foreground',
              )}
            >
              <span
                className={cn('h-2 w-2 rounded-full', t.id === 'marengo' ? 'bg-marengo' : 'bg-pegasus', tab === t.id && 'bg-black/70')}
              />
              {t.name}
            </button>
          ))}
        </div>

        {/* Keep both mounted so each tab retains its results while switching. */}
        <div className={cn(tab !== 'marengo' && 'hidden')} data-tab="marengo">
          <MarengoTab onAskPegasus={askPegasus} />
        </div>
        <div className={cn(tab !== 'pegasus' && 'hidden')} data-tab="pegasus">
          <PegasusTab seed={seed} />
        </div>
      </main>
      <footer className="mx-auto max-w-7xl px-4 pb-10 text-xs text-muted-foreground sm:px-6 lg:px-8">
        <div className="tl-hairline mb-4 opacity-40" />
        Data, models and agent run entirely inside Snowflake — Cortex Agents · Cortex Search multi-index · AI_MULTI_EMBED ·
        AI_COMPLETE.
      </footer>
    </div>
  );
}
