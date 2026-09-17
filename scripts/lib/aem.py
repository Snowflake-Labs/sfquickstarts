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
from typing import Any

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

# A copied node is not always readable the moment the copy request returns, so it
# is waited for rather than slept on: a write that lands before the copy does is
# silently undone when the copy finally arrives.
COPY_POLL_SECONDS = 2
COPY_WAIT_SECONDS = 90

# Writing a fragment is checked rather than assumed, and retried before it fails.
FRAGMENT_ATTEMPTS = 3
FRAGMENT_RETRY_SECONDS = 10

# The element a guide's markdown is written to, and the one worth reading back.
# The failure being caught replaces the body wholesale with the base template, so
# the opening of it is enough to tell the two apart. Comparing the whole value
# instead would turn any normalisation AEM applies into a permanent hard failure.
FRAGMENT_BODY_FIELD = "./data/master/quickstartArticleBody"
FRAGMENT_CHECK_CHARS = 500

# An asset is not indexed the moment its upload returns, and replication rejects
# one that is not, so activation waits first and a new asset waits much longer.
NEW_ASSET_SETTLE_SECONDS = 30
EXISTING_ASSET_SETTLE_SECONDS = 2
ACTIVATE_ATTEMPTS = 3
ACTIVATE_RETRY_SECONDS = 15

# A rate limit asks for a far longer pause than a server error does.
RATE_LIMIT_MULTIPLIER = 60

# How much of a failed response body to quote back in an error.
ERROR_BODY_CHARS = 500


class AemError(RuntimeError):
    """An AEM request failed."""


def author_url() -> str:
    """The AEM author instance to write to.

    The Secrets Manager payload calls it AEM_AUTHOR_URL, which is the name the
    secrets action exports when given a blank alias. AEM_URL is accepted too,
    because that is what the shell being replaced exported.
    """
    return os.environ.get("AEM_URL") or os.environ.get("AEM_AUTHOR_URL", "")


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
            author_url(),
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

    def wait_until_exists(self, path: str, description: str) -> None:
        """Block until a JCR path resolves, giving up loudly rather than late."""
        deadline = time.monotonic() + COPY_WAIT_SECONDS
        while not self.exists(path):
            if time.monotonic() >= deadline:
                msg = f"{description}: {path} did not appear within {COPY_WAIT_SECONDS}s"
                raise AemError(msg)
            time.sleep(COPY_POLL_SECONDS)

    def properties(self, path: str) -> dict[str, Any]:
        """Return a node's properties, or an empty mapping if it cannot be read."""
        status, raw = self._send("GET", f"{self.base_url}{path}.json", None)
        if not HTTP_OK <= status < HTTP_REDIRECT:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

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

    def write_fragment(self, cf_path: str, body: str, description: str) -> None:
        """Write a content fragment's payload and confirm the guide body took.

        A Sling POST answers 200 whether or not it wrote what was asked, so a write
        that races a still-settling copy of the base fragment is indistinguishable
        from a successful one: the fragment keeps the base template and the job goes
        green having staged an empty guide. The body is read back instead, and a
        fragment that cannot be confirmed fails the job.
        """
        expected = dict(urllib.parse.parse_qsl(body)).get(FRAGMENT_BODY_FIELD, "")
        opening = expected[:FRAGMENT_CHECK_CHARS]
        for attempt in range(1, FRAGMENT_ATTEMPTS + 1):
            self.post(f"{cf_path}/jcr:content", body, description)
            written = self.fragment_body(cf_path)
            if not expected or written.startswith(opening):
                return
            if attempt == FRAGMENT_ATTEMPTS:
                msg = (
                    f"{description}: {cf_path} does not hold the guide body after "
                    f"{FRAGMENT_ATTEMPTS} attempts (wrote {len(expected)} characters, "
                    f"read back {len(written)})"
                )
                raise AemError(msg)
            print(f"{description}: did not take, retrying in {FRAGMENT_RETRY_SECONDS}s")
            time.sleep(FRAGMENT_RETRY_SECONDS)

    def fragment_body(self, cf_path: str) -> str:
        """Return the guide body currently stored on a content fragment."""
        value = self.properties(f"{cf_path}/jcr:content/data/master").get("quickstartArticleBody")
        return value if isinstance(value, str) else ""

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

    def upload_asset(self, path: Path, dam_folder: str) -> bool:
        """Upload one image through the Assets API, returning whether it was created.

        PUT updates an existing asset and POST creates one. Which applies is probed
        first, but a PUT can still come back 404 because the probe races anything
        else writing to the folder, so that answer is taken as the correction it is
        rather than as a failed attempt.

        This writes to the author instance only. Anything that has to be readable on
        the public site needs publish_asset as well.
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
                return creating
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

    def reprocess_asset(self, asset_path: str) -> None:
        """Ask AEM to regenerate an asset's renditions.

        Best effort, as the shell this replaces had it: the publish tier falls back
        to the original when a rendition is missing, so a guide with unprocessed
        images still reads correctly.
        """
        fields = {"operation": "PROCESS", "asset": asset_path, "profile-select": "full-process"}
        body = urllib.parse.urlencode(fields).encode("utf-8")
        status, _ = self._send("POST", f"{self.base_url}/bin/asynccommand", body)
        if not HTTP_OK <= status < HTTP_REDIRECT:
            print(f"::warning::reprocessing {asset_path} returned HTTP {status}")

    def publish_asset(self, asset_path: str, *, created: bool) -> None:
        """Reprocess an uploaded asset and activate it to the publish tier.

        Replication answers 400 while an asset is still being indexed, which is a
        wait rather than a rejection and is the one 4xx worth retrying here.
        """
        self.reprocess_asset(asset_path)
        time.sleep(NEW_ASSET_SETTLE_SECONDS if created else EXISTING_ASSET_SETTLE_SECONDS)

        body = urllib.parse.urlencode({"cmd": "Activate", "path": asset_path}).encode("utf-8")
        for attempt in range(1, ACTIVATE_ATTEMPTS + 1):
            status, response = self._send("POST", f"{self.base_url}/bin/replicate.json", body)
            if HTTP_OK <= status < HTTP_REDIRECT:
                print(f"Published {asset_path}")
                return
            if status != HTTP_CLIENT_ERROR or attempt == ACTIVATE_ATTEMPTS:
                detail = response.decode("utf-8", errors="replace")[:ERROR_BODY_CHARS]
                msg = f"publishing {asset_path} failed (HTTP {status}): {detail}"
                raise AemError(msg)
            print(f"publishing {asset_path}: not indexed, retrying in {ACTIVATE_RETRY_SECONDS}s")
            time.sleep(ACTIVATE_RETRY_SECONDS)
