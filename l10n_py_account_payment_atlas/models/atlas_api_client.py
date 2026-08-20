# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

"""HTTP client for Banco Atlas (Paraguay) REST APIs.

Every Banco Atlas API (Consulta de Alias, Consulta de Saldo, Consulta de
Movimientos, Pago a Proveedores, Pago Salarios, Transferencias,
Transferencias Exterior) shares the same authentication scheme: an API
Key plus a JWT signed with the calling application's RSA private key, sent
as three HTTP headers (``X-RshkMichi-ApiKey``, ``X-Atl-Timestamp``,
``X-Atl-Auth``). This is *not* OAuth2 and *not* mTLS -- see the spec at
``docs/superpowers/specs`` (or the session's SIPAP/Atlas spec) for the
full breakdown of the scheme, sourced from the bank's own PDFs.
"""

import base64
import hashlib
import json

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def _b64url_encode(raw_bytes: bytes) -> str:
    """Base64url without padding, as required by JWT (RFC 7519)."""
    return base64.urlsafe_b64encode(raw_bytes).rstrip(b"=").decode()


class AtlasApiClient:
    """Client for one Banco Atlas bank account's credentials.

    Full constructor and ``call()``/``_verify_response_jwt()`` are added in
    Task 3; this task only adds the pure, database-free JWT builder so it
    can be unit-tested without an Odoo environment.
    """

    @staticmethod
    def build_jwt(
        private_key_pem: str,
        timestamp: str,
        resource: str,
        auth_token: str | None = None,
        content_hash: str | None = None,
    ) -> str:
        """Build the ``X-Atl-Auth`` JWT for one request.

        ``private_key_pem`` is the calling application's RSA private key
        (PEM, PKCS8, unencrypted -- Odoo already restricts read access to
        the field storing it via ``groups=``). ``timestamp`` must be the
        exact same string sent in the ``X-Atl-Timestamp`` header -- the
        bank's ``time`` claim must match it verbatim. ``resource`` is the
        request path, e.g. ``/proveedores/123456/registrar-pago``.
        ``auth_token`` and ``content_hash`` are omitted from the payload
        entirely when not given, per the bank's own JWT spec (they are
        optional/conditional claims, not claims sent as null).
        """
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {"time": timestamp, "resource": resource}
        if auth_token is not None:
            payload["auth"] = auth_token
        if content_hash is not None:
            payload["content-hash"] = content_hash

        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _b64url_encode(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        signing_input = f"{header_b64}.{payload_b64}".encode()

        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None
        )
        signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
        signature_b64 = _b64url_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @staticmethod
    def sha256_content_hash(raw_body: bytes) -> str:
        """SHA256 hex digest of a request body, for the ``content-hash``
        claim -- computed on the body *before* any additional encoding,
        per the bank's spec."""
        return hashlib.sha256(raw_body).hexdigest()
