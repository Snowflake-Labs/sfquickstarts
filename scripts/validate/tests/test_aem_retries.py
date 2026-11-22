"""Tests for transient AEM transport retries.

Run from the repository root with: python -m unittest discover -s scripts/validate/tests
"""

from __future__ import annotations

import sys
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SCRIPTS))

from lib import aem, upload_dam_asset  # noqa: E402


class _Response:
    def __init__(self, body: bytes = b"ok", error: Exception | None = None) -> None:
        self.status = 200
        self._body = body
        self._error = error

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        if self._error is not None:
            raise self._error
        return self._body


class AemRetryTest(unittest.TestCase):
    def client(self) -> aem.Client:
        client = aem.Client("https://author.example", "user", "password")
        client.attempts = 3
        client.delay = 1
        return client

    @mock.patch("lib.aem.time.sleep")
    @mock.patch("lib.aem.urllib.request.urlopen")
    def test_retries_read_timeout_with_bounded_backoff(
        self, urlopen: mock.Mock, sleep: mock.Mock
    ) -> None:
        urlopen.side_effect = [
            _Response(error=TimeoutError("read timed out")),
            _Response(body=b"complete"),
        ]

        status, body = self.client()._send_upload_request(
            "PUT", "https://author.example/asset", b"data"
        )

        self.assertEqual((status, body), (200, b"complete"))
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2)

    @mock.patch("lib.aem.time.sleep")
    @mock.patch("lib.aem.urllib.request.urlopen")
    def test_stops_after_configured_transport_attempts(
        self, urlopen: mock.Mock, sleep: mock.Mock
    ) -> None:
        urlopen.side_effect = urllib.error.URLError("temporarily unavailable")

        with self.assertRaisesRegex(aem.AemError, "failed after 3 attempts"):
            self.client()._send_upload_request("PUT", "https://author.example/asset", b"data")

        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [2, 4])

    @mock.patch("lib.upload_dam_asset.urllib.request.urlopen")
    def test_direct_upload_marks_timeout_retryable(self, urlopen: mock.Mock) -> None:
        urlopen.side_effect = TimeoutError("read timed out")
        uploader = upload_dam_asset.Uploader("https://author.example", "user", "password")

        with self.assertRaises(upload_dam_asset._RetryableError):
            uploader._request(
                "https://upload.example/asset",
                "PUT",
                b"data",
                "image/png",
                authenticate=False,
            )


if __name__ == "__main__":
    unittest.main()
