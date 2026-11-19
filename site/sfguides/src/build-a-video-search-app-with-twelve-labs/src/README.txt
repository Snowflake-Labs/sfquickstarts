# Video Intelligence Studio — Snowflake × Twelve Labs

Sample app for the [Build a Video Search App with Twelve Labs](../build-a-video-search-app-with-twelve-labs.md) guide. It's a Next.js app on Snowflake App Runtime (SAR) with two tabs, both orchestrated by one Cortex Agent:

- **Marengo**: multimodal moment search over the videos on `VIDEO_STAGE`, by text, an uploaded image, or an uploaded video clip.
  - Uses Cortex Search **multi-index** with three vector indexes: visual, speech/transcript and audio.
- **Pegasus**: video understanding with `twelvelabs-pegasus-1-5` on a staged video, a time range of one, or an uploaded video.
  - Presets: summary, chapters, highlights, brand safety and structured JSON.

## Snowflake objects (`TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE`)

Created by the guide's SQL steps:

| Object | Purpose |
| --- | --- |
| `VIDEO_STAGE` | Your videos, named `<video>.mp4` |
| `SEARCH_UPLOADS` | Internal stage (SSE) for user attachments and cached Pegasus clips |
| `VIDEO_SEGMENT_VECTORS` | One row per segment with `VISUAL_VEC` / `AUDIO_VEC` / `TRANSCRIPT_VEC` |
| `VIDEO_MULTI_SEARCH_SVC` | Cortex Search service with 3 vector indexes (`query_model='twelvelabs-marengo-embed-3-0'`) |

Created by [`setup.sql`](setup.sql):

| Object | Purpose |
| --- | --- |
| `MARENGO_SEARCH(query, file_path, modalities, episode)` | Embeds attachments with `AI_MULTI_EMBED`, queries each index, min-max normalizes and fuses scores, diversifies hits and presigns playback URLs |
| `CLIP_VIDEO(stage_name, file_path, start_sec, end_sec)` | Cuts a time range (stream copy, max 10 min) into `SEARCH_UPLOADS/clips/` |
| `PEGASUS_ANALYZE(prompt, stage_name, file_path, start_sec, end_sec)` | Runs `AI_COMPLETE('twelvelabs-pegasus-1-5', …, TO_FILE(…))`, clipping first when a range is given |
| `VIDEO_AGENT` | Cortex Agent with tools `MarengoSearch` and `PegasusAnalyze` |

Run it after the guide's SQL. Replace `COMPUTE_WH` with your warehouse first:

```bash
snow sql -f setup.sql
```

## Run locally

```bash
npm install
npm run dev            # uses your default snow CLI connection
npm test
```

Locally the agent route uses `SNOWFLAKE_PAT` if set; otherwise it runs `DATA_AGENT_RUN` over SQL and replays the result as SSE.

## Deploy

This needs a Snowflake CLI with the `snow app` command group (3.26+).

```bash
snow app setup --app-name=tl_video_studio --dry-run   # then without --dry-run
snow app deploy --verbose
```

After deploy, grant the app's owner role USAGE on `VIDEO_AGENT`, `VIDEO_MULTI_SEARCH_SVC`, the three procedures, `VIDEO_STAGE` and your warehouse, plus READ/WRITE on `SEARCH_UPLOADS`.

## Code map

- `app/api/agent`: proxies the agent `:run` SSE stream.
- `app/api/upload`: PUTs an image or video to `SEARCH_UPLOADS`.
- `app/api/videos`, `app/api/clip-url`: the Pegasus picker list and presigned preview URLs.
- `lib/constants.ts`: database, schema, stage and agent names.
- `lib/use-agent.ts`: SSE parser and agent state, used by both tabs.
- `components/marengo-tab.tsx`, `components/pegasus-tab.tsx`, `components/studio.tsx`: the UI.
