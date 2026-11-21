"""A small GitHub REST client built on the standard library.

The deploy jobs run with a write-scoped token. Keeping this client dependency-free
means no third-party package is ever installed next to that token, which is the
whole reason it exists rather than `requests`.
"""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, TypeAlias

# A decoded JSON document. Spelling this as a recursive union would force a cast at
# every access without catching anything real: the shape is whatever the API
# returned, and each caller already checks the fields it reads before using them.
Json: TypeAlias = Any

API_ROOT = "https://api.github.com"
USER_AGENT = "sfquickstarts-ci"
TIMEOUT_SECONDS = 30
MAX_ATTEMPTS = 4
MAX_PAGES = 50
RETRY_STATUSES = frozenset({403, 429, 500, 502, 503, 504})

# Guides hold markdown and screenshots. A blob past this is not content we stage,
# and decoding it would only burn runner memory.
MAX_BLOB_BYTES = 25 * 1024 * 1024

# A usable Link header part is a <url> plus at least one rel= parameter.
LINK_PART_SEGMENTS = 2


class GitHubError(RuntimeError):
    """A GitHub API request failed."""


def _next_link(header: str | None) -> str | None:
    if not header:
        return None
    for part in header.split(","):
        segments = part.split(";")
        if len(segments) < LINK_PART_SEGMENTS:
            continue
        target = segments[0].strip()
        if not target.startswith("<") or not target.endswith(">"):
            continue
        if any(segment.strip() == 'rel="next"' for segment in segments[1:]):
            return target[1:-1]
    return None


class GitHub:
    """The endpoints the CI scripts need, and nothing else."""

    def __init__(self, token: str, api_root: str = API_ROOT) -> None:
        if not token:
            msg = "a GitHub token is required"
            raise GitHubError(msg)
        self._token = token
        self._api_root = api_root.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _url(self, path: str, params: dict[str, str | int] | None = None) -> str:
        url = f"{self._api_root}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        return url

    def _send(self, url: str, method: str = "GET", payload: Json = None) -> tuple[Json, str | None]:
        if not url.startswith("https://"):
            msg = f"refusing to request a non-https url: {url!r}"
            raise GitHubError(msg)

        headers = self._headers()
        body: bytes | None = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(  # noqa: S310
            url, data=body, headers=headers, method=method
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
            decoded = json.loads(raw) if raw.strip() else None
            return decoded, _next_link(response.headers.get("Link"))

    def _get_with_retry(self, url: str) -> tuple[Json, str | None]:
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                return self._send(url)
            except urllib.error.HTTPError as exc:
                if exc.code not in RETRY_STATUSES or attempt == MAX_ATTEMPTS - 1:
                    msg = f"GET {url} failed with HTTP {exc.code}"
                    raise GitHubError(msg) from exc
                last_error = exc
            except urllib.error.URLError as exc:
                if attempt == MAX_ATTEMPTS - 1:
                    msg = f"GET {url} failed: {exc.reason}"
                    raise GitHubError(msg) from exc
                last_error = exc
            time.sleep(2**attempt)
        msg = f"GET {url} exhausted retries: {last_error}"
        raise GitHubError(msg)

    def get(self, path: str, params: dict[str, str | int] | None = None) -> Json:
        """Return the decoded body of a single GET."""
        payload, _ = self._get_with_retry(self._url(path, params))
        return payload

    def paginate(self, path: str, params: dict[str, str | int] | None = None) -> list[Json]:
        """Return every item across all pages, following the Link header."""
        url = self._url(path, params)
        items: list[Json] = []
        for _ in range(MAX_PAGES):
            payload, next_url = self._get_with_retry(url)
            if not isinstance(payload, list):
                msg = f"expected a JSON array from {path}"
                raise GitHubError(msg)
            items.extend(payload)
            if not next_url:
                return items
            url = next_url

        msg = f"pagination exceeded {MAX_PAGES} pages for {path}"
        raise GitHubError(msg)

    def blob(self, repo: str, blob_sha: str) -> bytes:
        """Return the bytes of one git blob.

        Content is fetched by object name rather than by building a
        raw.githubusercontent.com URL out of a branch name and a path, so nothing
        a contributor chooses ever reaches a URL.
        """
        payload = self.get(f"/repos/{repo}/git/blobs/{blob_sha}")
        if not isinstance(payload, dict):
            msg = f"blob {blob_sha} did not return an object"
            raise GitHubError(msg)

        size = payload.get("size")
        if isinstance(size, int) and size > MAX_BLOB_BYTES:
            msg = f"blob {blob_sha} is {size} bytes, over the {MAX_BLOB_BYTES} cap"
            raise GitHubError(msg)

        if payload.get("encoding") != "base64":
            msg = f"blob {blob_sha} has unexpected encoding {payload.get('encoding')!r}"
            raise GitHubError(msg)
        try:
            return base64.b64decode(payload.get("content") or "", validate=False)
        except (ValueError, TypeError) as exc:
            msg = f"blob {blob_sha} did not decode: {exc}"
            raise GitHubError(msg) from exc

    def post(self, path: str, payload: Json) -> Json:
        """Send a single POST.

        Deliberately not retried: a retry after a timeout could post the same
        comment twice, and a duplicate comment is worse than a failed step.
        """
        try:
            decoded, _ = self._send(self._url(path), method="POST", payload=payload)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            msg = f"POST {path} failed with HTTP {exc.code}: {detail}"
            raise GitHubError(msg) from exc
        except urllib.error.URLError as exc:
            msg = f"POST {path} failed: {exc.reason}"
            raise GitHubError(msg) from exc
        return decoded
