# Video Intelligence Studio — Snowflake × Twelve Labs

A Next.js app on Snowflake App Runtime (SAR) with two tabs, both orchestrated by a single Cortex Agent:

- **Marengo**: multimodal moment search over the 20 *Voyagers!* episodes. You can search by text, by an uploaded image, or by an uploaded video clip.
  - It uses Cortex Search **multi-index** with three vector indexes: visual, speech/transcript and audio.
  - Each index is tied to `twelvelabs-marengo-embed-3-0`, so text queries are embedded server-side.
- **Pegasus**: video understanding with `twelvelabs-pegasus-1-5`. It works on trailers, full episodes or an uploaded video.
  - Presets: summary, chapters, highlights, brand safety and structured JSON.

## Snowflake objects (`TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE`)

| Object | Purpose |
| --- | --- |
| `VIDEO_SEGMENT_VECTORS` | One row per ~6s segment, built by pivoting `VIDEO_EMBEDDINGS` into `VISUAL_VEC` / `AUDIO_VEC` / `TRANSCRIPT_VEC` |
| `VIDEO_MULTI_SEARCH_SVC` | Cortex Search service with 3 vector indexes (`query_model='twelvelabs-marengo-embed-3-0'`) |
| `MARENGO_SEARCH(query, file_path, modalities, episode)` | Proc. Embeds attachments with `AI_MULTI_EMBED` (file queries aren't supported by multi-index yet), applies per-index boosts, diversifies hits and presigns clip URLs |
| `PEGASUS_ANALYZE(prompt, stage_name, file_path)` | Proc. Runs `AI_COMPLETE('twelvelabs-pegasus-1-5', …, TO_FILE(…))`. Stage allowlist: TRAILERS / VOYAGERS / SEARCH_UPLOADS |
| `VIDEO_AGENT` | Cortex Agent (claude-sonnet-5-5) with tools MarengoSearch, PegasusAnalyze, VideoAnalyst (`VIDEO_ANALYTICS_SV`) and SceneSearch (`SCENE_SEARCH_SERVICE`) |
| `SEARCH_UPLOADS` | Internal stage (SSE) that holds user attachments |

The UI sends a context line on every message, such as `[tab=marengo] [attachment=…] [modalities=…]`. The agent's orchestration instructions use it to route to the right tool. Clip cards and Pegasus output are rendered from the agent's `tool_result` events.

## Code map

- `app/api/agent`: proxies the agent `:run` SSE stream.
  - In SAR it authenticates with the service OAuth token.
  - Locally it uses `SNOWFLAKE_PAT` if set; otherwise it runs `DATA_AGENT_RUN` over SQL and replays the result as SSE.
- `app/api/upload`: PUTs an image or video to `SEARCH_UPLOADS`.
- `app/api/videos`, `app/api/clip-url`: the Pegasus picker list and presigned preview URLs.
- `lib/use-agent.ts`: SSE parser and agent state, used by both tabs.
- `components/marengo-tab.tsx`, `components/pegasus-tab.tsx`, `components/studio.tsx`: the UI.
  - Brand tokens live in `app/globals.css`, based on the TL press kit plus Snowflake blue.

## Run locally

```bash
npm install
npm run dev            # uses your default snow CLI connection
npm test               # unset SNOWFLAKE_DEFAULT_CONNECTION_NAME first if it's set in your shell
```

## Deploy

This needs a Snowflake CLI with the `snow app` command group (3.26+).

```bash
snow app setup --app-name=tl_video_studio --dry-run   # then without --dry-run
snow app deploy --verbose
```

After deploy, grant the app's owner role USAGE on `VIDEO_AGENT`, `VIDEO_MULTI_SEARCH_SVC`, `SCENE_SEARCH_SERVICE`, `VIDEO_ANALYTICS_SV`, both procs, the stages and `COMPUTE_WH`. It also needs READ/WRITE on `SEARCH_UPLOADS`.
