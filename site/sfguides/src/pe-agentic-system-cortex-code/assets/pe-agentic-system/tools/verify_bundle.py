"""Validate bundled artifact integrity offline; never executes artifact code."""

import argparse
import hashlib
import json
from pathlib import Path


def verify_bundle(bundle, refresh=False):
    bundle = bundle.resolve()
    manifest = json.loads((bundle / "manifest.json").read_text())
    failures = []
    for name, expected in manifest["files"].items():
        artifact = (bundle / name).resolve()
        if not artifact.is_relative_to(bundle):
            failures.append(f"Path escapes bundle: {name}")
        elif not artifact.is_file():
            failures.append(f"Missing artifact: {name}")
        else:
            actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if refresh:
                manifest["files"][name] = actual
            elif actual != expected:
                failures.append(f"Hash mismatch: {name}")
    skill = "skills/waterfall-reconciliation-review/SKILL.md"
    if refresh:
        manifest["skill_sha256"] = manifest["files"].get(skill)
    elif manifest["skill_sha256"] != manifest["files"].get(skill):
        failures.append("skill_sha256 differs from the skill file manifest entry")
    if failures:
        raise SystemExit("\n".join(failures))
    if refresh:
        (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verified {len(manifest['files'])} artifact hashes and the skill hash.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true",
        help="Refresh hashes only after manually reviewing every changed artifact.",
    )
    args = parser.parse_args()
    verify_bundle(Path(__file__).resolve().parents[1] / "generated", args.refresh)