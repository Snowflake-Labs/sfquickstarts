/** App title — displayed in the nav header and browser tab */
export const APP_TITLE = 'Video Intelligence Studio';

/** Path to the logo in /public (used as favicon) */
export const LOGO_SRC = '/icon.svg';

/**
 * Pages listed under "Go to" in the ⌘K command palette.
 */
export const NAV_ITEMS: { label: string; href: string }[] = [
  { label: 'Marengo — Search', href: '/?tab=marengo' },
  { label: 'Pegasus — Analyze', href: '/?tab=pegasus' },
];

/** Fully qualified Snowflake objects the app talks to. */
export const DB = 'TWELVE_LABS_DEMO';
export const SCHEMA = 'VIDEO_INTELLIGENCE';
export const AGENT_NAME = 'VIDEO_AGENT';
export const UPLOAD_STAGE = `${DB}.${SCHEMA}.SEARCH_UPLOADS`;

/** Stages the Pegasus picker can read from (must match PEGASUS_ANALYZE allowlist). */
export const PEGASUS_STAGES = ['TRAILERS_STAGE', 'VOYAGERS_STAGE', 'SEARCH_UPLOADS'] as const;
export type PegasusStage = (typeof PEGASUS_STAGES)[number];

export type Modality = 'visual' | 'transcript' | 'audio';
export const MODALITIES: { id: Modality; label: string }[] = [
  { id: 'visual', label: 'Visual' },
  { id: 'transcript', label: 'Speech' },
  { id: 'audio', label: 'Audio' },
];

export const PEGASUS_PRESETS: { label: string; prompt: string }[] = [
  { label: 'Summary', prompt: 'Summarize this video in 3 sentences, then list the 5 most important moments with mm:ss timestamps.' },
  { label: 'Chapters', prompt: 'Break this video into chapters. For each give a mm:ss start, a short title and a one-line description.' },
  {
    label: 'Highlights',
    prompt: 'Identify the 5 most shareable highlight moments for social media with mm:ss timestamps and a suggested caption for each.',
  },
  {
    label: 'Ad & brand safety',
    prompt:
      'Review this video for brand safety. Rate violence, language and mature themes 1-5, list any risky moments with mm:ss timestamps, and recommend ad categories that fit.',
  },
  {
    label: 'Structured JSON',
    prompt:
      'Return ONLY JSON with keys: title, genre, mood, setting, characters (array), key_objects (array), scenes (array of {start, end, description}).',
  },
];
