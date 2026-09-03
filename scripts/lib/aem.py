"""Talk to an AEM author instance over its HTTP API.

Credentials only ever exist as an Authorization header value, never on a command
line where they would be visible in the process table.

The retry policy is the one AEM needs rather than a generic one: a 429 asks for a
much longer pause than a server error, and a 4xx is a request the instance will
keep rejecting, so it fails immediately instead of burning the remaining attempts.

Standard library only, so the jobs holding AEM credentials install nothing.

Environment:
    AEM_URL, AEM_USERNAME, AEM_PASSWORD  target instance and credentials
    MAX_RETRIES   attempts before giving up (default 3)
    RETRY_DELAY   base seconds for the backoff (default 5)
"""

from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT_SECONDS = 120
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5

HTTP_OK = 200
HTTP_REDIRECT = 300
HTTP_CLIENT_ERROR = 400
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVER_ERROR = 500

FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"
JSON_CONTENT_TYPE = "application/json"

# AEM creates a folder asynchronously, so the first upload into it has to wait.
FOLDER_SETTLE_SECONDS = 3

# A rate limit asks for a far longer pause than a server error does.
RATE_LIMIT_MULTIPLIER = 60

# How much of a failed response body to quote back in an error.
ERROR_BODY_CHARS = 500


class AemError(RuntimeError):
    """An AEM request failed."""


def asset_content_type(name: str) -> str:
    """Content type for an image, derived from its extension as the shell did."""
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if extension == "jpg":
        return "image/jpeg"
    if extension == "svg":
        return "image/svg+xml"
    return f"image/{extension}" if extension else "application/octet-stream"


def retry_delay(status: int, attempt: int, base: int) -> int | None:
    """Seconds to wait before retrying, or None when the request must not be retried."""
    if status == HTTP_TOO_MANY_REQUESTS:
        return base * RATE_LIMIT_MULTIPLIER
    if status >= HTTP_SERVER_ERROR:
        return base * attempt * 2
    if HTTP_CLIENT_ERROR <= status < HTTP_SERVER_ERROR:
        return None
    return base * attempt


class Client:
    """One AEM instance, addressed with basic auth."""

    def __init__(self, base_url: str, username: str, password: str) -> None:
        if not base_url or not username or not password:
            msg = "AEM_URL, AEM_USERNAME and AEM_PASSWORD are all required"
            raise AemError(msg)
        if not base_url.startswith("https://"):
            msg = f"refusing to talk to a non-https AEM instance: {base_url!r}"
            raise AemError(msg)
        self.base_url = base_url.rstrip("/")
        token = base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
        self._auth = f"Basic {token}"
        self.attempts = int(os.environ.get("MAX_RETRIES") or DEFAULT_MAX_RETRIES)
        self.delay = int(os.environ.get("RETRY_DELAY") or DEFAULT_RETRY_DELAY)

    @classmethod
    def from_env(cls) -> Client:
        """Build a client from the credentials the workflow exported."""
        return cls(
            os.environ.get("AEM_URL", ""),
            os.environ.get("AEM_USERNAME", ""),
            os.environ.get("AEM_PASSWORD", ""),
        )

    def _send(
        self,
        method: str,
        url: str,
        body: bytes | None,
        content_type: str = FORM_CONTENT_TYPE,
    ) -> tuple[int, bytes]:
        headers = {"Authorization": self._auth}
        if body is not None:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=body, headers=headers, method=method)  # noqa: S310
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:  # noqa: S310
                return response.status, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
        except urllib.error.URLError as exc:
            msg = f"{method} {url} failed: {exc.reason}"
            raise AemError(msg) from exc

    def status(self, path: str) -> int:
        """Return the status of a single unretried GET, for existence checks."""
        code, _ = self._send("GET", f"{self.base_url}{path}", None)
        return code

    def exists(self, path: str) -> bool:
        """Whether a JCR path resolves on the instance."""
        return self.status(f"{path}.json") == HTTP_OK

    def post(self, path: str, body: str, description: str) -> bytes:
        """POST a pre-encoded form body, retrying what is worth retrying."""
        url = f"{self.base_url}{path}"
        payload = body.encode("utf-8")
        last = b""
        for attempt in range(1, self.attempts + 1):
            status, last = self._send("POST", url, payload)
            if HTTP_OK <= status < HTTP_REDIRECT:
                return last
            wait = retry_delay(status, attempt, self.delay)
            detail = last.decode("utf-8", errors="replace")[:ERROR_BODY_CHARS]
            if wait is None or attempt == self.attempts:
                msg = f"{description} failed (HTTP {status}): {detail}"
                raise AemError(msg)
            print(f"{description}: HTTP {status}, retrying in {wait}s")
            time.sleep(wait)
        msg = f"{description} failed after {self.attempts} attempts"
        raise AemError(msg)

    def post_fields(self, path: str, fields: dict[str, str], description: str) -> bytes:
        """POST form fields, encoding them first."""
        return self.post(path, urllib.parse.urlencode(fields), description)

    def copy(self, source: str, dest: str, description: str, *, deep: bool = False) -> None:
        """Copy a JCR node, replacing whatever is at the destination."""
        fields = {":operation": "copy", ":dest": dest, ":replace": "true"}
        if deep:
            fields["depth"] = "infinity"
        self.post_fields(source, fields, description)

    def replicate(self, path: str, description: str) -> None:
        """Activate a path so it reaches the publish tier."""
        self.post_fields("/bin/replicate.json", {"cmd": "Activate", "path": path}, description)

    def ensure_asset_folder(self, dam_folder: str) -> None:
        """Create a DAM folder if it is missing.

        Two ways of doing the same thing, because the Assets API is the documented
        route but is not always enabled; the Sling POST underneath it always is.
        """
        if self.exists(dam_folder):
            return

        parent, _, name = dam_folder.rpartition("/")
        relative_parent = parent.removeprefix("/content/dam/")
        body = json.dumps(
            {"class": "assetFolder", "properties": {"name": name, "title": name}}
        ).encode("utf-8")

        print(f"Creating DAM folder: {dam_folder}")
        status, _ = self._send(
            "POST", f"{self.base_url}/api/assets/{relative_parent}/*", body, JSON_CONTENT_TYPE
        )
        if not HTTP_OK <= status < HTTP_REDIRECT:
            print(f"Assets API returned {status}; falling back to a Sling POST")
            self.post_fields(
                parent,
                {"./jcr:primaryType": "sling:OrderedFolder", ":name": name},
                "create DAM folder",
            )
        time.sleep(FOLDER_SETTLE_SECONDS)

    def upload_asset(self, path: Path, dam_folder: str) -> None:
        """Upload one image through the Assets API.

        PUT updates an existing asset and POST creates one. Which applies is probed
        first, but a PUT can still come back 404 because the probe races anything
        else writing to the folder, so that answer is taken as the correction it is
        rather than as a failed attempt.
        """
        encoded = urllib.parse.quote(path.name, safe="")
        url = f"{self.base_url}/api/assets/{dam_folder.removeprefix('/content/dam/')}/{encoded}"
        content_type = asset_content_type(path.name)
        body = path.read_bytes()

        creating = self.status(f"{dam_folder}/{encoded}") != HTTP_OK
        attempt = 1
        while attempt <= self.attempts:
            method = "POST" if creating else "PUT"
            status, response = self._send(method, url, body, content_type)
            if HTTP_OK <= status < HTTP_REDIRECT:
                print(f"Uploaded {path.name} ({method}, HTTP {status})")
                return
            if status == HTTP_NOT_FOUND and not creating:
                creating = True
                continue
            wait = retry_delay(status, attempt, self.delay)
            if wait is None:
                detail = response.decode("utf-8", errors="replace")[:ERROR_BODY_CHARS]
                msg = f"upload of {path.name} failed (HTTP {status}): {detail}"
                raise AemError(msg)
            print(f"upload of {path.name}: HTTP {status}, retrying in {wait}s")
            time.sleep(wait)
            attempt += 1

        msg = f"upload of {path.name} failed after {self.attempts} attempts"
        raise AemError(msg)
