import os
import re
import json
import subprocess
from typing import Dict, List, Optional


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
BASE_URL = "https://www.snowflake.com/en/developers/guides/"


def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def get_last_updated(path: str) -> Optional[str]:
    try:
        rel = os.path.relpath(path, REPO_ROOT)
        out = subprocess.check_output(
            ["git", "-C", REPO_ROOT, "log", "-1", "--format=%cs", rel],
            stderr=subprocess.DEVNULL,
        )
        return out.decode().strip() or None
    except Exception:
        return None


def parse_front_matter(text: str) -> Dict[str, str]:
    """
    Parses the top contiguous block of key: value lines as 'front matter'.
    Stops at the first blank or non key:value line.
    """
    meta: Dict[str, str] = {}
    lines = text.splitlines()
    for line in lines:
        if not line.strip():
            break
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip().lower()] = val.strip()
        else:
            break
    return meta


def extract_title(text: str) -> Optional[str]:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def find_md_file(folder: str) -> Optional[str]:
    md_candidates = [f for f in os.listdir(folder) if f.lower().endswith(".md")]
    if not md_candidates:
        return None
    folder_name = os.path.basename(folder)
    for f in md_candidates:
        if os.path.splitext(f)[0] == folder_name:
            return os.path.join(folder, f)
    md_paths = [os.path.join(folder, f) for f in md_candidates]
    md_paths.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return md_paths[0]


def normalize_categories(raw_cat: Optional[str]) -> List[str]:
    if not raw_cat:
        return []
    rc = raw_cat.strip()
    # JSON-like array
    if rc.startswith("[") and rc.endswith("]"):
        try:
            val = json.loads(rc)
            if isinstance(val, list):
                return [str(x) for x in val]
        except Exception:
            return [rc]
    # CSV list
    if "," in rc:
        return [c.strip() for c in rc.split(",") if c.strip()]
    # taxonomy path — use last segment
    if "/" in rc:
        return [rc.split("/")[-1]]
    return [rc]


def build_manifest() -> Dict[str, List[Dict[str, str]]]:
    entries: List[Dict[str, str]] = []
    for name in sorted(os.listdir(SRC_DIR)):
        if name.startswith(".") or name.startswith("_"):
            continue
        folder = os.path.join(SRC_DIR, name)
        if not os.path.isdir(folder):
            continue
        md_path = find_md_file(folder)
        if not md_path:
            continue
        text = read_text(md_path)
        if not text:
            continue

        meta = parse_front_matter(text)
        title = extract_title(text) or meta.get("title") or name.replace("-", " ").title()
        summary = meta.get("summary", "")
        categories = normalize_categories(meta.get("categories"))
        duration = meta.get("duration") or meta.get("estimated_time") or meta.get("estimated_read_time")
        if duration:
            duration = str(duration).strip().strip("\"")
        url = BASE_URL + name + "/"
        last_updated = get_last_updated(md_path) or get_last_updated(folder) or ""

        entry: Dict[str, str] = {
            "title": title,
            "categories": categories,
            "contentType": "quickstart",
            "url": url,
            "summary": summary,
            "lastUpdatedAt": last_updated,
        }
        if duration:
            entry["duration"] = duration

        entries.append(entry)
    return {"quickstartMetadata": entries}


def main() -> None:
    manifest = build_manifest()
    out_path = os.path.join(SRC_DIR, "quickstart-manifest.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_path} with {len(manifest.get('quickstartMetadata', []))} entries.")


if __name__ == "__main__":
    main()


