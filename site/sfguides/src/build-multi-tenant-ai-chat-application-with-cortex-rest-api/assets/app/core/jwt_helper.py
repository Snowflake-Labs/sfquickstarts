import time
import hashlib
import base64
import logging
from pathlib import Path

import jwt
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    Encoding,
    PublicFormat,
)
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("coco.jwt")

REFRESH_MARGIN_SECONDS = 300


class JWTGenerator:
    def __init__(self, account, user, private_key_path,
                 private_key_passphrase="", lifetime_seconds=3540):
        self.account = account.upper().split(".")[0].replace(".", "-")
        self.user = user.upper()
        self.qualified_username = f"{self.account}.{self.user}"
        self.private_key_path = private_key_path
        self.private_key_passphrase = private_key_passphrase
        self.lifetime_seconds = lifetime_seconds

        self._private_key = None
        self._public_key_fp = None
        self._cached_token: str = ""
        self._cached_expiry: float = 0.0

    def _load_private_key(self):
        if self._private_key is not None:
            return

        pem_data = Path(self.private_key_path).read_bytes()
        passphrase = (self.private_key_passphrase.encode()
                      if self.private_key_passphrase else None)

        self._private_key = load_pem_private_key(
            pem_data, passphrase, default_backend()
        )

        pub_der = self._private_key.public_key().public_bytes(
            Encoding.DER, PublicFormat.SubjectPublicKeyInfo
        )
        sha256 = hashlib.sha256(pub_der).digest()
        self._public_key_fp = "SHA256:" + base64.b64encode(sha256).decode()

        logger.info("Loaded key for %s (fp: %s...)",
                    self.qualified_username, self._public_key_fp[:20])

    def get_token(self) -> str:
        now = time.time()

        if self._cached_token and (self._cached_expiry - now) > REFRESH_MARGIN_SECONDS:
            return self._cached_token

        self._load_private_key()

        iat = int(now)
        exp = iat + self.lifetime_seconds

        payload = {
            "iss": f"{self.qualified_username}.{self._public_key_fp}",
            "sub": self.qualified_username,
            "iat": iat,
            "exp": exp,
        }

        token = jwt.encode(payload, self._private_key, algorithm="RS256")
        self._cached_token = token if isinstance(token, str) else token.decode()
        self._cached_expiry = float(exp)
        return self._cached_token
