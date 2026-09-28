#!/usr/bin/env python3
"""Upload a file to the AEM DAM using the three-step direct binary upload.

Credentials only ever exist as an Authorization header value, never on a command
line where they would be visible in the process table.

Standard library only, so the job holding AEM credentials installs nothing.

Usage:
    upload_dam_asset.py <file-path> <dam-folder>

Environment:
    AEM_URL, AEM_USERNAME, AEM_PASSWORD  target instance and credentials
    MAX_RETRIES   attempts before giving up (default 3)
    RETRY_DELAY   base seconds for the backoff (default 5)
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from lib import aem

TIMEOUT_SECONDS = 120
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
# AEM needs a moment between the three calls; the shell slept for the same reason.
SETTLE_SECONDS = 2

# HTTP status boundaries, named so the comparisons below read as intent.
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_REDIRECT = 300
HTTP_SERVER_ERROR = 500


class UploadError(RuntimeError):
    """The asset could not be uploaded."""


class Uploader:
    """One AEM instance, addressed with basic auth."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        if not base_url or not username or not password:
            msg = "AEM_URL, AEM_USERNAME and AEM_PASSWORD are all required"
            raise UploadError(msg)
        if not base_url.startswith("https://"):
            msg = f"refusing to talk to a non-https AEM instance: {base_url!r}"
            raise UploadError(msg)
        self._base_url = base_url.rstrip("/")
        token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
        self._auth = f"Basic {token}"

    def _request(
        self,
        url: str,
        method: str,
        data: bytes | None,
        content_type: str | None,
        authenticate: bool,
    ) -> tuple[int, bytes]:
        headers = {}
        if authenticate:
            headers["Authorization"] = self._auth
        if content_type:
            headers["Content-Type"] = content_type

        request = urllib.request.Request(url, data=data, headers=headers, method=method)  # noqa: S310
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
        except urllib.error.URLError as exc:
            msg = f"{method} {url} failed: {exc.reason}"
            raise UploadError(msg) from exc

    def _form(self, url: str, fields: dict[str, str]) -> tuple[int, bytes]:
        body = urllib.parse.urlencode(fields).encode("utf-8")
        return self._request(
            url, "POST", body, "application/x-www-form-urlencoded", authenticate=True
        )

    def initiate(self, dam_folder: str, name: str, size: int) -> dict[str, Any]:
        """Ask AEM where to put the bytes."""
        url = f"{self._base_url}/content/dam/{dam_folder}.initiateUpload.json"
        status, body = self._form(url, {"fileName": name, "fileSize": str(size)})
        if not HTTP_OK <= status < HTTP_REDIRECT:
            raise _retryable(status, f"initiate upload failed (HTTP {status})", body)

        payload = json.loads(body.decode("utf-8"))
        files = payload.get("files") or []
        if not files or not files[0].get("uploadURIs"):
            msg = "AEM returned no upload URI"
            raise UploadError(msg)
        return {
            "upload_uri": files[0]["uploadURIs"][0],
            "upload_token": files[0].get("uploadToken", ""),
            "mime_type": files[0].get("mimeType") or "application/octet-stream",
            "complete_uri": payload.get("completeURI", ""),
        }

    def put_binary(self, upload_uri: str, content: bytes, mime_type: str) -> None:
        """Send the bytes to the location AEM handed back.

        Unauthenticated on purpose: the URI is pre-signed, and attaching the AEM
        credentials would leak them to whatever storage backend it points at.
        """
        status, _ = self._request(upload_uri, "PUT", content, mime_type, authenticate=False)
        if status not in (HTTP_OK, HTTP_CREATED):
            raise _retryable(status, f"binary upload failed (HTTP {status})", b"")

    def complete(self, complete_uri: str, name: str, token: str, mime_type: str) -> None:
        """Tell AEM the bytes have landed."""
        url = f"{self._base_url}{complete_uri}"
        status, body = self._form(
            url,
            {
                "fileName": name,
                "uploadToken": token,
                "mimeType": mime_type,
                "createVersion": "true",
            },
        )
        if not HTTP_OK <= status < HTTP_REDIRECT:
            raise _retryable(status, f"complete upload failed (HTTP {status})", body)


class _RetryableError(UploadError):
    """A failure that is worth another attempt."""


def _retryable(status: int, message: str, body: bytes) -> UploadError:
    detail = body.decode("utf-8", errors="replace")[:500]
    text = f"{message}: {detail}" if detail else message
    return _RetryableError(text) if status >= HTTP_SERVER_ERROR else UploadError(text)


def upload_once(uploader: Uploader, path: Path, dam_folder: str) -> None:
    """Run the three-step upload for one file."""
    content = path.read_bytes()
    session = uploader.initiate(dam_folder, path.name, len(content))

    mime_type = session["mime_type"]
    if mime_type == "application/octet-stream":
        guessed, _ = mimetypes.guess_type(path.name)
        mime_type = guessed or mime_type

    time.sleep(SETTLE_SECONDS)
    uploader.put_binary(session["upload_uri"], content, mime_type)
    time.sleep(SETTLE_SECONDS)
    uploader.complete(session["complete_uri"], path.name, session["upload_token"], mime_type)


def upload(path: Path, dam_folder: str) -> None:
    """Upload one file, retrying only failures that AEM might recover from."""
    if not path.is_file():
        msg = f"file not found: {path}"
        raise UploadError(msg)

    uploader = Uploader(
        aem.author_url(),
        os.environ.get("AEM_USERNAME", ""),
        os.environ.get("AEM_PASSWORD", ""),
    )
    attempts = int(os.environ.get("MAX_RETRIES") or DEFAULT_MAX_RETRIES)
    delay = int(os.environ.get("RETRY_DELAY") or DEFAULT_RETRY_DELAY)

    print(f"Uploading {path.name} ({path.stat().st_size} bytes) to /content/dam/{dam_folder}/")
    for attempt in range(1, attempts + 1):
        try:
            upload_once(uploader, path, dam_folder)
        except _RetryableError as exc:
            if attempt == attempts:
                raise
            wait = delay * attempt * 2
            print(f"Attempt {attempt} of {attempts} failed: {exc}; retrying in {wait}s")
            time.sleep(wait)
            continue
        print(f"Uploaded to /content/dam/{dam_folder}/{path.name}")
        return


def main() -> int:
    """Upload the file named on the command line."""
    parser = argparse.ArgumentParser(description="Upload a file to the AEM DAM.")
    parser.add_argument("file_path", type=Path)
    parser.add_argument("dam_folder")
    args = parser.parse_args()

    upload(args.file_path, args.dam_folder)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except UploadError as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
