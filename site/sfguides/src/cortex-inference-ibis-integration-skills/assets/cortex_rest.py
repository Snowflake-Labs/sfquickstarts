"""
cortex_rest.py — Direct Snowflake Cortex Inference REST API client.

Covers:
  - PAT (Programmatic Access Token) auth — reads from ~/.snowflake/config.toml
  - JWT key-pair auth — signs with PyJWT + RSA private key
  - CortexInferenceClient: complete(), complete_stream(), with full SSE parsing
  - Module-level helpers: complete(), stream()

Endpoint:
  POST /api/v2/cortex/inference:complete

Auth header variants:
  PAT:  Authorization: Bearer <token>
        X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN

  JWT:  Authorization: Bearer <signed_jwt>
        X-Snowflake-Authorization-Token-Type: KEYPAIR_JWT

Install:
  pip install httpx PyJWT cryptography

Quick start:
  from cortex_rest import CortexInferenceClient
  client = CortexInferenceClient()          # auto-loads PAT from config.toml
  resp = client.complete("claude-4-sonnet", [{"role": "user", "content": "ping"}])
  print(resp["choices"][0]["message"]["content"])
"""

from __future__ import annotations

import json
import tomllib
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Generator, Optional, Union

import httpx

# ──────────────────────────────────────────────────────────────────────────────
# Auth helpers
# ──────────────────────────────────────────────────────────────────────────────

_CONFIG_PATH = Path.home() / ".snowflake" / "config.toml"
_DEFAULT_CONNECTION = "myaccount"


def _load_pat(connection: str = _DEFAULT_CONNECTION) -> tuple[str, str]:
    """
    Read account host + PAT from ~/.snowflake/config.toml.
    Returns (host, token).
    """
    with open(_CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    conn = cfg["connections"][connection]
    host = conn["host"]            # e.g. myorg-myaccount.snowflakecomputing.com
    token = conn["password"]       # PAT stored as password field
    return host, token


def _build_jwt(
    account: str,
    user: str,
    private_key_path: Union[str, Path],
    passphrase: Optional[bytes] = None,
    lifetime_minutes: int = 60,
) -> str:
    """
    Build a signed Snowflake JWT from an RSA private key.

    Snowflake JWT format:
      iss = <ACCOUNT>.<USER>.<fingerprint>
      sub = <ACCOUNT>.<USER>
      iat = now
      exp = now + lifetime
    """
    try:
        import jwt as pyjwt
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes, serialization
    except ImportError as exc:
        raise ImportError(
            "JWT auth requires: pip install PyJWT cryptography"
        ) from exc

    key_data = Path(private_key_path).read_bytes()
    private_key = serialization.load_pem_private_key(
        key_data, password=passphrase, backend=default_backend()
    )

    # Compute public key fingerprint (SHA256, base64url)
    pub_key = private_key.public_key()
    pub_der = pub_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(pub_der)
    fingerprint = "SHA256:" + __import__("base64").b64encode(digest.finalize()).decode()

    acct = account.upper().split(".")[0]   # strip region suffix if present
    usr  = user.upper()

    now = datetime.now(tz=timezone.utc)
    payload = {
        "iss": f"{acct}.{usr}.{fingerprint}",
        "sub": f"{acct}.{usr}",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=lifetime_minutes)).timestamp()),
    }
    return pyjwt.encode(payload, private_key, algorithm="RS256")


# ──────────────────────────────────────────────────────────────────────────────
# REST client
# ──────────────────────────────────────────────────────────────────────────────

class CortexInferenceClient:
    """
    Thin httpx-based client for the Snowflake Cortex inference:complete endpoint.

    Usage (PAT, auto-loaded from config.toml):
        client = CortexInferenceClient()

    Usage (explicit PAT):
        client = CortexInferenceClient(auth="pat", pat="<token>",
                                       host="myorg-myaccount.snowflakecomputing.com")

    Usage (JWT key-pair):
        client = CortexInferenceClient(
            auth="jwt",
            account="myorg-myaccount",
            user="you@example.com",
            private_key_path="~/.ssh/snowflake_rsa_key.p8",
        )
    """

    def __init__(
        self,
        *,
        auth: str = "pat",
        connection: str = _DEFAULT_CONNECTION,
        pat: Optional[str] = None,
        host: Optional[str] = None,
        account: Optional[str] = None,
        user: Optional[str] = None,
        private_key_path: Optional[Union[str, Path]] = None,
        private_key_passphrase: Optional[bytes] = None,
        timeout: float = 120.0,
    ) -> None:
        if auth == "pat":
            _host, _token = _load_pat(connection)
            self._host = host or _host
            self._token = pat or _token
            self._auth_type = "PROGRAMMATIC_ACCESS_TOKEN"
        elif auth == "jwt":
            if not all([account, user, private_key_path]):
                raise ValueError("JWT auth requires: account, user, private_key_path")
            self._host = host or f"{account.split('.')[0].lower()}.snowflakecomputing.com"
            self._token = _build_jwt(account, user, private_key_path, private_key_passphrase)
            self._auth_type = "KEYPAIR_JWT"
        else:
            raise ValueError(f"Unknown auth type: {auth!r}. Use 'pat' or 'jwt'.")

        self._base_url = f"https://{self._host}/api/v2/cortex"
        self._client = httpx.Client(timeout=timeout)

    @property
    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self._token}",
            "X-Snowflake-Authorization-Token-Type": self._auth_type,
        }

    def complete(
        self,
        model: str,
        messages: list[dict],
        *,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[Union[str, dict]] = None,
        **kwargs,
    ) -> dict:
        """
        Non-streaming chat completion.

        Returns the parsed JSON response dict with keys:
          id, model, choices[].message.content, usage.{prompt,completion,total}_tokens
        """
        payload: dict = {"model": model, "messages": messages, "stream": False}
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        payload.update(kwargs)

        resp = self._client.post(
            f"{self._base_url}/inference:complete",
            headers=self._headers,
            content=json.dumps(payload),
        )
        resp.raise_for_status()
        return resp.json()

    def complete_stream(
        self,
        model: str,
        messages: list[dict],
        *,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
        **kwargs,
    ) -> Generator[dict, None, None]:
        """
        Streaming chat completion. Yields parsed SSE event dicts.

        Each yielded dict has the Snowflake SSE shape:
          {"id": ..., "model": ..., "choices": [{"delta": {"content": "..."}}], "usage": {}}

        The last event carries usage.{prompt,completion,total}_tokens.
        """
        payload: dict = {"model": model, "messages": messages, "stream": True, "max_tokens": max_tokens}
        if temperature is not None:
            payload["temperature"] = temperature
        payload.update(kwargs)

        with self._client.stream(
            "POST",
            f"{self._base_url}/inference:complete",
            headers=self._headers,
            content=json.dumps(payload),
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[len("data:"):].strip()
                if data_str == "[DONE]":
                    return
                try:
                    yield json.loads(data_str)
                except json.JSONDecodeError:
                    continue

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ──────────────────────────────────────────────────────────────────────────────
# Module-level convenience (singleton client)
# ──────────────────────────────────────────────────────────────────────────────

_default_client: Optional[CortexInferenceClient] = None


def _get_client() -> CortexInferenceClient:
    global _default_client
    if _default_client is None:
        _default_client = CortexInferenceClient()
    return _default_client


def complete(
    prompt: str,
    *,
    model: str = "claude-4-sonnet",
    max_tokens: int = 512,
    system: Optional[str] = None,
) -> str:
    """Quick one-shot completion. Returns the assistant reply as a string."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = _get_client().complete(model, messages, max_tokens=max_tokens)
    return resp["choices"][0]["message"]["content"]


def stream(
    prompt: str,
    *,
    model: str = "claude-4-sonnet",
    max_tokens: int = 512,
) -> Generator[str, None, None]:
    """Quick streaming completion. Yields text chunks."""
    messages = [{"role": "user", "content": prompt}]
    for event in _get_client().complete_stream(model, messages, max_tokens=max_tokens):
        delta = event.get("choices", [{}])[0].get("delta", {})
        chunk = delta.get("content") or delta.get("text", "")
        if chunk:
            yield chunk
