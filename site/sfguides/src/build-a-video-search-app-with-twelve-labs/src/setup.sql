-- Setup for the Twelve Labs video search guide.
-- Run AFTER the guide's SQL steps (VIDEO_STAGE, SEARCH_UPLOADS, VIDEO_SEGMENT_VECTORS,
-- VIDEO_MULTI_SEARCH_SVC). Creates the procedures and Cortex Agent the app calls.
-- Video files on VIDEO_STAGE must be named <video>.mp4, matching VIDEO_EMBEDDINGS.episode.
-- Replace COMPUTE_WH below with your warehouse.

USE SCHEMA TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE;

-- Cut a time range out of a staged video (stream copy) into SEARCH_UPLOADS/clips/.
CREATE OR REPLACE PROCEDURE "CLIP_VIDEO"("STAGE_NAME" VARCHAR, "FILE_PATH" VARCHAR, "START_SEC" FLOAT, "END_SEC" FLOAT)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python','av')
HANDLER = 'run'
COMMENT='Cuts [start,end] from a staged video (stream copy, no re-encode) into SEARCH_UPLOADS/clips/ for Pegasus; cached by name'
EXECUTE AS OWNER
AS '
import hashlib, os, tempfile
import av
from snowflake.snowpark.files import SnowflakeFile

ALLOWED = {"VIDEO_STAGE", "SEARCH_UPLOADS"}
DEST = "@TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.SEARCH_UPLOADS/clips"
MAX_LEN = 600.0

def _lit(s):
    return "''" + str(s).replace("\\\\", "\\\\\\\\").replace("''", "''''") + "''"

def run(session, stage_name, file_path, start_sec, end_sec):
    stage = (stage_name or "").upper().lstrip("@").split(".")[-1]
    if stage not in ALLOWED or not file_path:
        return {"error": "invalid stage or file"}
    start = max(0.0, float(start_sec or 0))
    end = float(end_sec) if end_sec is not None else start + 60
    end = min(max(end, start + 5), start + MAX_LEN)

    key = hashlib.md5(f"{stage}/{file_path}/{start:.1f}/{end:.1f}".encode()).hexdigest()[:12]
    name = f"clip_{key}_{int(start)}_{int(end)}.mp4"
    rel = f"clips/{name}"
    exists = session.sql(
        f"SELECT COUNT(*) AS N FROM DIRECTORY(@TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.SEARCH_UPLOADS) WHERE RELATIVE_PATH = {_lit(rel)}"
    ).collect()[0]["N"]
    if exists:
        return {"stage": "SEARCH_UPLOADS", "file": rel, "start_sec": start, "end_sec": end, "cached": True}

    src_url = f"@TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.{stage}/{file_path}"
    out_dir = tempfile.mkdtemp()
    out_path = os.path.join(out_dir, name)
    with SnowflakeFile.open(src_url, "rb", require_scoped_url=False) as f:
        inp = av.open(f)
        out = av.open(out_path, "w", format="mp4")
        streams = [s for s in inp.streams if s.type in ("video", "audio")]
        omap = {s.index: out.add_stream_from_template(s) for s in streams}
        vs = next((s for s in streams if s.type == "video"), streams[0])
        inp.seek(int(start / vs.time_base), stream=vs, backward=True, any_frame=False)
        first = {}
        for pkt in inp.demux(streams):
            if pkt.dts is None or pkt.pts is None:
                continue
            t = float(pkt.pts * pkt.stream.time_base)
            if t > end:
                if pkt.stream.type == "video":
                    break
                continue
            base = first.setdefault(pkt.stream.index, pkt.dts)
            pkt.pts -= base
            pkt.dts -= base
            pkt.stream = omap[pkt.stream.index]
            out.mux(pkt)
        out.close()
        inp.close()

    session.file.put(out_path, DEST, auto_compress=False, overwrite=True)
    session.sql("ALTER STAGE TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.SEARCH_UPLOADS REFRESH").collect()
    size = os.path.getsize(out_path)
    os.remove(out_path)
    return {"stage": "SEARCH_UPLOADS", "file": rel, "start_sec": start, "end_sec": end, "bytes": size, "cached": False}
';

-- Multi-index Marengo search with per-index normalization and weighted fusion.
CREATE OR REPLACE PROCEDURE "MARENGO_SEARCH"("QUERY" VARCHAR, "FILE_PATH" VARCHAR DEFAULT null, "MODALITIES" VARCHAR DEFAULT 'visual,transcript,audio', "EPISODE" VARCHAR DEFAULT null)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run'
COMMENT='Twelve Labs Marengo multi-index search; per-index score normalization + weighted fusion across visual/transcript/audio'
EXECUTE AS OWNER
AS '
import json

SVC = "TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.VIDEO_MULTI_SEARCH_SVC"
UPLOADS = "@TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.SEARCH_UPLOADS"
VIDEOS = "@TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.VIDEO_STAGE"
INDEX = {"visual": "VISUAL_VEC", "transcript": "TRANSCRIPT_VEC", "audio": "AUDIO_VEC"}
OPTION = {"visual": "visual", "audio": "audio", "transcription": "transcript"}
# Applied AFTER per-index normalization, so they express intent, not scale correction.
WEIGHT = {"visual": 1.0, "transcript": 0.8, "audio": 0.5}
CANDIDATES = 100

def _lit(s):
    return "''" + str(s).replace("\\\\", "\\\\\\\\").replace("''", "''''") + "''"

def _embed_file(session, path):
    row = session.sql(
        f"SELECT AI_MULTI_EMBED(''twelvelabs-marengo-embed-3-0'', TO_FILE(''{UPLOADS}'', {_lit(path)})) AS r"
    ).collect()[0]
    vecs = {}
    for v in json.loads(row["R"])["value"]:
        mod = OPTION.get(v.get("embedding_option") or "visual", "visual")
        if v.get("embedding_scope") in (None, "asset") or mod not in vecs:
            vecs[mod] = v["embedding"]
    return vecs

def _search_index(session, col, q, episode):
    req = {"multi_index_query": {col: [q]}, "columns": ["SEGMENT_ID", "EPISODE", "START_SEC", "END_SEC"], "limit": CANDIDATES}
    if episode:
        req["filter"] = {"@eq": {"EPISODE": episode}}
    raw = session.sql("SELECT SNOWFLAKE.CORTEX.SEARCH_PREVIEW(?, ?) AS r", params=[SVC, json.dumps(req)]).collect()[0]["R"]
    return json.loads(raw).get("results", [])

def run(session, query, file_path, modalities, episode):
    mods = [m.strip() for m in (modalities or "visual,transcript,audio").split(",") if m.strip() in INDEX] or list(INDEX)
    vecs = _embed_file(session, file_path) if file_path else {}

    # One query per index. Raw cosine scales differ a lot by modality (text->transcript is
    # same-modality and scores ~4x higher than text->visual), so min-max normalize within each index.
    segs, norm, raw_scores = {}, {}, {}
    used = []
    for m in mods:
        if m in vecs:
            q = {"vector": vecs[m]}
        elif query:
            q = {"text": query}
        else:
            continue
        hits = _search_index(session, INDEX[m], q, episode)
        if not hits:
            continue
        used.append(m)
        sc = [float(h["@scores"]["cosine_similarity"]) for h in hits]
        hi, lo = max(sc), min(sc)
        span = (hi - lo) or 1.0
        for h, s in zip(hits, sc):
            sid = h["SEGMENT_ID"]
            segs[sid] = h
            norm.setdefault(sid, {})[m] = (s - lo) / span
            raw_scores.setdefault(sid, {})[m] = s
    if not used:
        return {"error": "Provide a text query or an attachment.", "results": []}

    wsum = sum(WEIGHT[m] for m in used)
    fused = sorted(
        ((sum(WEIGHT[m] * norm[sid].get(m, 0.0) for m in used) / wsum, sid) for sid in segs),
        reverse=True)

    # Diversify: <=2 per episode, >=45s apart, 8 results.
    kept, out = {}, []
    for score, sid in fused:
        h = segs[sid]
        ep, start = h["EPISODE"], float(h["START_SEC"])
        prior = kept.get(ep, [])
        if len(prior) >= 2 or any(abs(start - p) < 45 for p in prior):
            continue
        kept[ep] = prior + [start]
        out.append({
            "segment_id": sid, "episode": ep, "start_sec": start, "end_sec": float(h["END_SEC"]),
            "score": round(score, 4),
            "modality_scores": {m: {"normalized": round(norm[sid].get(m, 0.0), 4),
                                    "raw": round(raw_scores[sid].get(m, 0.0), 4),
                                    "weight": WEIGHT[m]} for m in used},
        })
        if len(out) >= 8:
            break

    urls = {}
    for ep in {r["episode"] for r in out}:
        try:
            urls[ep] = session.sql(
                f"SELECT GET_PRESIGNED_URL({VIDEOS}, {_lit(ep + ''.mp4'')}, 3600) AS u").collect()[0]["U"]
        except Exception:
            urls[ep] = None
    for r in out:
        r["video_url"] = urls.get(r["episode"])
    return {"query": query, "attachment": file_path, "modalities": used,
            "fusion": "per-index min-max normalization, weighted sum", "results": out}
';

-- Pegasus 1.5 analysis of a staged video, optionally on a clipped time range.
CREATE OR REPLACE PROCEDURE "PEGASUS_ANALYZE"("PROMPT" VARCHAR, "STAGE_NAME" VARCHAR, "FILE_PATH" VARCHAR, "START_SEC" FLOAT DEFAULT null, "END_SEC" FLOAT DEFAULT null)
RETURNS VARIANT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run'
COMMENT='Twelve Labs Pegasus analysis of a staged video; optional time range is clipped via CLIP_VIDEO first (use it for long videos)'
EXECUTE AS OWNER
AS '
import json

ALLOWED = {"VIDEO_STAGE", "SEARCH_UPLOADS"}
# Add a stage here to force callers to pass a time range (e.g. a stage of very long videos).
NEEDS_RANGE = set()

def _lit(s):
    return "''" + str(s).replace("\\\\", "\\\\\\\\").replace("''", "''''") + "''"

def run(session, prompt, stage_name, file_path, start_sec, end_sec):
    stage = (stage_name or "VIDEO_STAGE").upper().lstrip("@").split(".")[-1]
    if stage not in ALLOWED:
        return {"error": f"Stage must be one of {sorted(ALLOWED)}"}
    if not file_path:
        return {"error": "file_path is required"}
    if stage in NEEDS_RANGE and start_sec is None:
        return {"error": "Videos on this stage are too long for Pegasus. Pass start_sec and end_sec (up to 10 minutes)."}

    source = {"stage": stage, "file": file_path}
    clip = None
    if start_sec is not None:
        clip = session.call("TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.CLIP_VIDEO", stage, file_path, float(start_sec),
                            float(end_sec) if end_sec is not None else None)
        clip = json.loads(clip) if isinstance(clip, str) else clip
        if clip.get("error"):
            return clip
        stage, file_path = clip["stage"], clip["file"]

    ref = f"@TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.{stage}"
    text = session.sql(
        f"SELECT AI_COMPLETE(''twelvelabs-pegasus-1-5'', ?, TO_FILE(''{ref}'', {_lit(file_path)})) AS a",
        params=[prompt]).collect()[0]["A"]
    if isinstance(text, str) and text.startswith(''"''):
        try:
            text = json.loads(text)
        except ValueError:
            pass
    if not text:
        return {"error": "Pegasus returned no output for this video.", **source}
    out = {"stage": source["stage"], "file": source["file"], "analysis": text}
    if clip:
        out.update({"clip_file": clip["file"], "start_sec": clip["start_sec"], "end_sec": clip["end_sec"],
                    "note": "Timestamps in the analysis are relative to start_sec."})
    return out
';

-- Cortex Agent the app talks to.
CREATE OR REPLACE AGENT VIDEO_AGENT
  COMMENT = 'Twelve Labs Marengo search + Pegasus analysis over VIDEO_STAGE'
  FROM SPECIFICATION $$
{
  "models": {
    "orchestration": "claude-sonnet-5-5"
  },
  "orchestration": {
    "budget": {
      "seconds": 180,
      "tokens": 24000
    },
    "tool_not_accessible": "accept"
  },
  "instructions": {
    "response": "You are the Snowflake x Twelve Labs video intelligence assistant for the videos on VIDEO_STAGE.\nBe concise. When you cite clips always give the video name and the timestamp as mm:ss. Do not paste raw URLs or vectors. Use short markdown bullets.\nWhen PegasusAnalyze returns start_sec, its timestamps are relative to that clip: convert them to video time (add start_sec) before reporting.\n",
    "orchestration": "Each user message may start with a context line like:\n[tab=marengo|pegasus] [attachment=<file on SEARCH_UPLOADS or none>] [stage=<STAGE>] [file=<path>] [range=<start_sec>-<end_sec>]\nRouting rules:\n- tab=marengo, or the user wants to FIND / SEE / locate moments: call MarengoSearch once with the user's words as query. If an attachment is present pass it as file_path. Always search all modalities (omit the modalities argument).\n- tab=pegasus, or the user wants a summary / description / chapters / highlights / moderation / Q&A about one specific video: call PegasusAnalyze ONCE with stage_name and file_path from the context line (an attachment means stage SEARCH_UPLOADS). If a range is given pass start_sec and end_sec exactly. Write a focused prompt for Pegasus. Do not retry PegasusAnalyze with the same arguments; if it returns an error, explain it briefly.\n- You may chain tools, e.g. MarengoSearch to find a moment then PegasusAnalyze on that range.\n",
    "sample_questions": [
      {
        "question": "Find me a scene where a ship is burning at night"
      },
      {
        "question": "Summarize this video and list its key moments"
      }
    ]
  },
  "tools": [
    {
      "tool_spec": {
        "type": "generic",
        "name": "MarengoSearch",
        "description": "Twelve Labs Marengo multimodal moment search over the videos on VIDEO_STAGE using Cortex Search multi-index (visual, transcript and audio vector indexes, normalized and fused). Accepts natural language and/or an uploaded image or video clip as a search-by-example query. Returns up to 8 diversified clips with video name, start_sec, end_sec, fused score and a playable video_url.",
        "input_schema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "Natural-language description of the moment to find. May be empty when file_path is given."
            },
            "file_path": {
              "type": "string",
              "description": "Optional relative path of an uploaded image or clip on SEARCH_UPLOADS to search by example."
            },
            "episode": {
              "type": "string",
              "description": "Optional exact video name (file name without .mp4) to restrict results."
            }
          },
          "required": [
            "query"
          ]
        }
      }
    },
    {
      "tool_spec": {
        "type": "generic",
        "name": "PegasusAnalyze",
        "description": "Twelve Labs Pegasus 1.5 video understanding model. Watches one staged video (or a time range of it) and answers a prompt: summaries, chapters with timestamps, highlights, moderation review, structured JSON, Q&A. When start_sec/end_sec are given (max 10 minutes) the range is clipped server-side before Pegasus watches it.",
        "input_schema": {
          "type": "object",
          "properties": {
            "prompt": {
              "type": "string",
              "description": "Instruction for Pegasus about the video."
            },
            "stage_name": {
              "type": "string",
              "description": "One of VIDEO_STAGE, SEARCH_UPLOADS."
            },
            "file_path": {
              "type": "string",
              "description": "Relative path of the video on that stage."
            },
            "start_sec": {
              "type": "number",
              "description": "Optional clip start in seconds."
            },
            "end_sec": {
              "type": "number",
              "description": "Optional clip end in seconds (at most start_sec + 600)."
            }
          },
          "required": [
            "prompt",
            "stage_name",
            "file_path"
          ]
        }
      }
    }
  ],
  "tool_resources": {
    "MarengoSearch": {
      "type": "procedure",
      "identifier": "TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.MARENGO_SEARCH",
      "execution_environment": {
        "type": "warehouse",
        "warehouse": "COMPUTE_WH",
        "query_timeout": 120
      }
    },
    "PegasusAnalyze": {
      "type": "procedure",
      "identifier": "TWELVE_LABS_DEMO.VIDEO_INTELLIGENCE.PEGASUS_ANALYZE",
      "execution_environment": {
        "type": "warehouse",
        "warehouse": "COMPUTE_WH",
        "query_timeout": 400
      }
    }
  }
}
$$;
