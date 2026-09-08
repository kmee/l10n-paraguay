# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

"""HTTP client for Banco Itaú Paraguay's Open Banking (IOB) REST APIs.

Itaú's channel authenticates at the TRANSPORT layer via a client
certificate (mTLS) plus an IP whitelist configured on the bank's portal
("24 Horas Negocios" > Open Banking > Suscripción al canal) -- this is a
genuinely different scheme from Banco Atlas's JWT/RSA-signed-header
approach (``l10n_py_account_payment_atlas``'s ``AtlasApiClient``): do not
copy that pattern here, mTLS has no per-request signature to build.

KNOWN GAP (documented, not an oversight): the bank's own commercial PDFs
(``docs/backlog/Open Banking Itaú - *.pdf`` in the elm-template repo, not
in this codebase) confirm the channel exists and describe the onboarding
flow, but the actual endpoint paths, JSON request/response schemas, and
whether an additional per-operation "token de canal" header is required
on top of mTLS are ONLY published inside the bank's own portal, under
"Documentación de APIs" -- gated behind completing the digital
subscription and assigning an operator with "Desarrollador" permission.
Nobody has that access yet (as of this module's creation, 2026-09-08).

Consequently, this client is deliberately a thin, generic transport layer
(mTLS + JSON + uniform error handling) with NO endpoint-specific methods
(contrast with ``AtlasApiClient.consultar_alias``/``consultar_banco_exterior``,
which encode confirmed, bank-documented paths). Adding endpoint-specific
methods here before the real documentation exists would be committing a
guess as if it were confirmed behavior -- exactly what this integration's
plan (see elm-template docs/superpowers/plans/2026-09-08-itau-py-open-
banking-integracao.md) explicitly avoids. Fase 3 of that plan is where
those methods get added, once the real docs are in hand.
"""

import base64
import logging
import os
import tempfile

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ItauApiClient:
    """Client for one Banco Itaú Open Banking (IOB)-enabled bank account.

    The client certificate and private key are stored on the bank
    account as binary fields (not filesystem paths -- Odoo workers are
    not guaranteed to share a filesystem, and a hardcoded path would not
    survive a multi-worker/cloud deployment). ``call()`` materializes
    them into a temporary file pair for the lifetime of a single request
    and always removes them afterwards, including on error.
    """

    def __init__(
        self,
        environment_url: str,
        client_cert_pem: bytes,
        client_key_pem: bytes,
        ruc_empresa: str | None = None,
        codigo_empresa: str | None = None,
        canal_token: str | None = None,
    ):
        self.environment_url = environment_url.rstrip("/")
        self.client_cert_pem = client_cert_pem
        self.client_key_pem = client_key_pem
        self.ruc_empresa = ruc_empresa
        self.codigo_empresa = codigo_empresa
        # Placeholder: the security slide of the bank's presentation
        # deck lists "Token de canal para validar cada operación" as a
        # security layer distinct from mTLS + IP whitelist + iToken, but
        # gives no detail on how it is obtained or which header carries
        # it. Wired through here so Fase 3 only has to fill in the
        # header name once confirmed, not restructure the client.
        self.canal_token = canal_token

    @classmethod
    def from_bank_account(cls, bank_account):
        """Build a client from an Itaú-enabled ``res.partner.bank``
        record. Raises a clear ``UserError`` for every misconfiguration,
        same discipline as ``AtlasApiClient.from_bank_account``."""
        if not bank_account or not bank_account.itau_enabled:
            raise UserError(
                _(
                    "Esta cuenta bancaria no está configurada para el "
                    "Banco Itaú Open Banking (falta habilitar 'Banco "
                    "Itaú (Open Banking)' en la cuenta bancaria)."
                )
            )
        if not bank_account.itau_client_cert or not bank_account.itau_client_key:
            raise UserError(
                _(
                    "La cuenta bancaria '%(account)s' no tiene el "
                    "certificado mTLS y/o la clave privada configurados "
                    "para el canal Itaú Open Banking.",
                    account=bank_account.display_name,
                )
            )
        if (
            bank_account.itau_environment == "production"
            and not bank_account.itau_production_url
        ):
            raise UserError(
                _(
                    "La cuenta bancaria '%(account)s' está configurada "
                    "para el entorno de Producción del Banco Itaú, pero "
                    "no tiene la URL de producción configurada. "
                    "Complétela antes de continuar.",
                    account=bank_account.display_name,
                )
            )
        # NOTE: no known/confirmed sandbox URL exists yet for Itaú IOB
        # (unlike Banco Atlas, whose testing URL is public knowledge --
        # see AtlasApiClient.from_bank_account). "testing" therefore has
        # no default here on purpose: forcing an explicit URL avoids
        # silently pointing at a guessed host.
        environment_urls = {
            "testing": bank_account.itau_production_url or "",
            "production": bank_account.itau_production_url or "",
        }
        base_url = environment_urls.get(bank_account.itau_environment or "", "")
        if not base_url:
            raise UserError(
                _(
                    "La cuenta bancaria '%(account)s' no tiene una URL "
                    "de entorno Itaú Open Banking configurada. No existe "
                    "un endpoint de testing público y confirmado para "
                    "este banco (a diferencia de Banco Atlas) -- "
                    "complete la URL provista por el banco.",
                    account=bank_account.display_name,
                )
            )
        return cls(
            environment_url=base_url,
            # res.partner.bank's cert/key are ``fields.Binary`` -- Odoo's
            # ORM returns their content already base64-encoded, never
            # the raw PEM bytes. Decode once here so the client (and its
            # temp-file writer) always deals in raw bytes.
            client_cert_pem=base64.b64decode(bank_account.itau_client_cert),
            client_key_pem=base64.b64decode(bank_account.itau_client_key),
            ruc_empresa=bank_account.itau_ruc_empresa,
            codigo_empresa=bank_account.itau_codigo_empresa,
            canal_token=bank_account.itau_canal_token,
        )

    def call(self, method: str, path: str, body: dict | None = None) -> dict:
        """Perform one Itaú IOB API call over mTLS.

        Raises ``ItauApiError`` for any HTTP status other than 200/201,
        and for transport-level failures (connection errors, timeouts,
        non-JSON responses). Does not retry.

        The exact header(s) required beyond the mTLS handshake itself
        (e.g. the "token de canal" mentioned in the bank's security
        overview, or a company/RUC header) are UNCONFIRMED -- see this
        module's docstring. What is sent below is deliberately minimal
        (``Content-Type`` only) and marked for revision in Fase 3.
        """
        if not self.client_cert_pem or not self.client_key_pem:
            raise ItauApiError(
                status_code=None,
                message=_(
                    "Falta configurar el certificado mTLS y/o la clave "
                    "privada de Banco Itaú Open Banking en esta cuenta "
                    "bancaria."
                ),
            )

        cert_path, key_path = self._write_temp_cert_pair()
        try:
            headers = {"Content-Type": "application/json"}
            if self.canal_token:
                # Placeholder header name -- unconfirmed (see docstring).
                headers["X-Itau-Canal-Token"] = self.canal_token
            try:
                response = requests.request(
                    method,
                    f"{self.environment_url}{path}",
                    headers=headers,
                    json=body,
                    cert=(cert_path, key_path),
                    timeout=30,
                )
            except requests.exceptions.RequestException as exc:
                raise ItauApiError(
                    status_code=None,
                    message=_(
                        "No se pudo conectar con el Banco Itaú Open "
                        "Banking (%(url)s): %(error)s",
                        url=f"{self.environment_url}{path}",
                        error=str(exc),
                    ),
                ) from exc
        finally:
            self._remove_temp_files(cert_path, key_path)

        if response.status_code not in (200, 201):
            raw_excerpt = (response.text or "")[:200]
            try:
                error_body = response.json()
            except ValueError:
                error_body = None
            raise ItauApiError(
                status_code=response.status_code,
                message=(
                    (error_body or {}).get("message")
                    or (error_body or {}).get("error")
                    or raw_excerpt
                ),
                body=error_body,
            )

        try:
            return response.json()
        except ValueError as exc:
            raw_excerpt = (response.text or "")[:200]
            raise ItauApiError(
                status_code=response.status_code,
                message=_(
                    "El Banco Itaú devolvió una respuesta no-JSON (HTTP "
                    "%(status)s): %(excerpt)r",
                    status=response.status_code,
                    excerpt=raw_excerpt,
                ),
            ) from exc

    def _write_temp_cert_pair(self) -> tuple[str, str]:
        """Materialize the stored cert/key into a private temp file pair
        for the duration of one request. ``requests``' ``cert=`` option
        only accepts filesystem paths, not in-memory PEM bytes."""
        cert_fd, cert_path = tempfile.mkstemp(suffix=".pem")
        key_fd, key_path = tempfile.mkstemp(suffix=".pem")
        try:
            with os.fdopen(cert_fd, "wb") as cert_file:
                cert_file.write(self.client_cert_pem)
            with os.fdopen(key_fd, "wb") as key_file:
                key_file.write(self.client_key_pem)
        except Exception:
            self._remove_temp_files(cert_path, key_path)
            raise
        os.chmod(key_path, 0o600)
        return cert_path, key_path

    @staticmethod
    def _remove_temp_files(*paths: str) -> None:
        for path in paths:
            try:
                os.remove(path)
            except OSError:
                _logger.warning(
                    "Could not remove temporary mTLS cert/key file %s "
                    "(it may contain sensitive material -- check manually).",
                    path,
                )


class ItauApiError(UserError):
    """Raised for any non-2xx response from an Itaú IOB API, and for
    transport-level failures (connection errors, timeouts, non-JSON
    responses).

    Unlike ``AtlasApiError``, there is no confirmed, uniform error body
    shape for Itaú yet -- ``body`` carries the raw parsed JSON (or
    ``None``) through for whatever inspection Fase 3 turns out to need,
    rather than assuming field names that have not been confirmed.
    """

    def __init__(self, status_code, message, body=None):
        self.status_code = status_code
        self.message = message
        self.body = body
        super().__init__(f"[HTTP {status_code}] {message}")
