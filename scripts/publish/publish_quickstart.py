#!/usr/bin/env python3
"""Publish one guide to AEM.

Runs on a job holding production AEM credentials. Workflow inputs arrive through
env: and are validated here before they reach a path or a URL.

Standard library only, so nothing is installed next to those credentials. The
markdown parsing runs as a separate process, which is where PyYAML lives.

The AEM calls themselves are placeholders in this repository.

Environment:
    QUICKSTART_NAME  guide folder name
    LANGUAGE         content language
    COMMIT_SHA       commit being published
    BASE_IMAGE_URL   base URL rewritten into image references
    SOURCE_PATH      guide folder, when it is not under site/sfguides/src
    PAGE_BASE_PATH   page template to clone from, when not the default
    AWS_SECRET_NAME  secret the workflow fetched AEM credentials from
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from lib import validate

AEM_STAGING = Path(__file__).resolve().parent.parent / "aem-staging"
PARSE_MARKDOWN = AEM_STAGING / "parse_markdown.py"
PREPARE_PAYLOAD = AEM_STAGING / "prepare_aem_payload.py"

QUICKSTART_ROOT = "site/sfguides/src"
CF_DEST_PATH = "/content/dam/snowflake-site"
BASE_CF_PATH = "/content/dam/snowflake-site/en/content-fragments/base-fragments/base-quickstart-cf"
PAGE_BASE_PATH_DEFAULT = "/content/snowflake-site/global/en/developers/guides/quickstart-base"
DAM_GUIDES_PATH = "/content/dam/snowflake-site/developers/guides"
PAGE_ROOT = "/content/snowflake-site/global"

PARSED_JSON = Path("parsed_content.json")
PAYLOAD_JSON = Path("aem_payload.json")

IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp", ".ico", ".tiff")


class PublishError(RuntimeError):
    """The guide could not be published."""


def placeholder(message: str) -> None:
    """Record an AEM call this repository deliberately does not make."""
    print(f"[PLACEHOLDER] {message}")


@dataclass(frozen=True)
class Target:
    """One guide, with everything needed to place it in AEM."""

    name: str
    language: str
    commit_sha: str
    base_image_url: str
    source_path: Path
    page_base_path: str

    @property
    def content_fragment(self) -> str:
        return f"{CF_DEST_PATH}/{self.language}/content-fragments/quickstarts/{self.name}"

    @property
    def page(self) -> str:
        return f"{PAGE_ROOT}/{self.language}/developers/guides/{self.name}"

    @property
    def dam_folder(self) -> str:
        return f"{DAM_GUIDES_PATH}/{self.name}"


def _base_image_url(value: str | None) -> str:
    if not value or not value.startswith("https://"):
        msg = f"base image url must be an https url, got {value!r}"
        raise PublishError(msg)
    if any(char in value for char in " \"'\\<>"):
        msg = f"base image url contains disallowed characters: {value!r}"
        raise PublishError(msg)
    return value.rstrip("/")


def read_target() -> Target:
    """Validate every workflow input before it is used to build a path."""
    name = validate.guide_name(os.environ.get("QUICKSTART_NAME"))
    raw_source = os.environ.get("SOURCE_PATH") or f"{QUICKSTART_ROOT}/{name}"
    source_path = Path(validate.repo_path(raw_source))

    page_base = os.environ.get("PAGE_BASE_PATH") or PAGE_BASE_PATH_DEFAULT
    if not page_base.startswith("/content/"):
        msg = f"page base path must sit under /content/, got {page_base!r}"
        raise PublishError(msg)

    return Target(
        name=name,
        language=validate.language(os.environ.get("LANGUAGE") or validate.DEFAULT_LANGUAGE),
        commit_sha=validate.sha40(os.environ.get("COMMIT_SHA")),
        base_image_url=_base_image_url(os.environ.get("BASE_IMAGE_URL")),
        source_path=source_path,
        page_base_path=page_base,
    )


def find_markdown(target: Target) -> Path:
    """Return the guide's markdown file."""
    if not target.source_path.is_dir():
        msg = f"source folder not found: {target.source_path}"
        raise PublishError(msg)

    preferred = target.source_path / f"{target.name}.md"
    if preferred.is_file():
        return preferred
    found = next((p for p in sorted(target.source_path.glob("*.md")) if p.is_file()), None)
    if found is None:
        msg = f"no markdown file found in {target.source_path}"
        raise PublishError(msg)
    return found


def _run(command: list[str], description: str) -> None:
    result = subprocess.run(command, check=False)  # noqa: S603
    if result.returncode != 0:
        msg = f"{description} failed with exit code {result.returncode}"
        raise PublishError(msg)


def parse(target: Target, markdown: Path) -> None:
    """Extract the guide's content and build the AEM content fragment payload."""
    _run(
        [
            sys.executable,
            str(PARSE_MARKDOWN),
            str(markdown),
            "--commit-sha",
            target.commit_sha,
            "--quickstart-name",
            target.name,
            "--base-image-url",
            target.base_image_url,
            "--strip-assets-prefix",
            "--output-json",
            str(PARSED_JSON),
        ],
        "markdown parse",
    )
    _run(
        [
            sys.executable,
            str(PREPARE_PAYLOAD),
            str(PARSED_JSON),
            "--content-fragment-path",
            target.content_fragment,
            "--language",
            target.language,
            "--output-json",
            str(PAYLOAD_JSON),
        ],
        "payload preparation",
    )


def status_of() -> str:
    """Return the publication status the guide declares."""
    if not PARSED_JSON.is_file():
        return "Draft"
    try:
        parsed = json.loads(PARSED_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "Draft"
    status = parsed.get("status") if isinstance(parsed, dict) else None
    return status if isinstance(status, str) and status else "Draft"


def publish_content_fragment(target: Target) -> None:
    """Create or update the guide's content fragment."""
    placeholder(f"Would check whether content fragment exists: {target.content_fragment}")
    placeholder(f"Would copy base fragment {BASE_CF_PATH} if it is new")
    placeholder(f"Would update content fragment from {PAYLOAD_JSON}")
    placeholder(f"Would publish content fragment: {target.content_fragment}")


def publish_images(target: Target) -> int:
    """Upload the guide's images to the DAM."""
    assets = target.source_path / "assets"
    images = (
        sorted(
            path
            for path in assets.iterdir()
            if path.is_file() and not path.is_symlink() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        if assets.is_dir()
        else []
    )

    placeholder(f"Would ensure DAM folder exists: {target.dam_folder}")
    for image in images:
        # The real call is upload_dam_asset.upload(image, dam_folder without /content/dam/).
        placeholder(f"Would upload {image.name} to {target.dam_folder}")
    return len(images)


def publish_page(target: Target, status: str) -> None:
    """Create or update the guide's page, publishing it when it is ready."""
    placeholder(f"Would check whether page exists: {target.page}")
    placeholder(f"Would create page from {target.page_base_path} if it is new")
    placeholder(f"Would update page content at: {target.page}")
    if status == "Published":
        placeholder(f"Would publish page: {target.page}")
    else:
        print(f"Status is {status}; leaving the page unpublished")


def summarise(target: Target, markdown: Path, status: str, image_count: int) -> None:
    """Print what this run would have done."""
    print("\nPublish summary")
    print(f"  Guide:            {target.name}")
    print(f"  Language:         {target.language}")
    print(f"  Commit:           {target.commit_sha}")
    print(f"  Markdown:         {markdown}")
    print(f"  Status:           {status}")
    print(f"  Content fragment: {target.content_fragment}")
    print(f"  Page:             {target.page}")
    print(f"  Images:           {image_count}")
    print(f"  Secret:           {os.environ.get('AWS_SECRET_NAME', '(unset)')}")


def main() -> int:
    """Publish one guide."""
    target = read_target()
    markdown = find_markdown(target)
    print(f"Publishing {target.name} from {markdown}")

    parse(target, markdown)
    status = status_of()

    publish_content_fragment(target)
    image_count = publish_images(target)
    publish_page(target, status)
    summarise(target, markdown, status, image_count)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (PublishError, validate.ValidationError) as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
