# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import os
from unittest import mock

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_py_account_payment_itau.models.itau_api_client import (
    ItauApiClient,
    ItauApiError,
)

_TEST_CERT_PEM = b"-----BEGIN CERTIFICATE-----\ntest-cert\n-----END CERTIFICATE-----\n"
_TEST_KEY_PEM = b"-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n"


def _client(canal_token=None):
    return ItauApiClient(
        environment_url="https://openbanking.itau.com.py/sandbox",
        client_cert_pem=_TEST_CERT_PEM,
        client_key_pem=_TEST_KEY_PEM,
        ruc_empresa="80012345-6",
        codigo_empresa="123456",
        canal_token=canal_token,
    )


@tagged("post_install", "-at_install", "l10n_py")
class TestItauApiClientCall(TransactionCase):
    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_uses_mtls_cert_pair(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=200, json=lambda: {"ok": True}, headers={}
        )
        _client().call("GET", "/business-account/v1/cuentas")
        _, kwargs = mock_request.call_args
        cert_path, key_path = kwargs["cert"]
        # By the time we inspect the call, the client has already
        # cleaned up the temp files -- this test only proves the request
        # itself was built with a (cert, key) path pair, not that the
        # files survive after the call (they must NOT, see the cleanup
        # test below).
        self.assertTrue(cert_path.endswith(".pem"))
        self.assertTrue(key_path.endswith(".pem"))

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_removes_temp_cert_files_after_request(self, mock_request):
        captured = {}

        def _fake_request(
            method, url, headers=None, json=None, cert=None, timeout=None
        ):
            captured["cert_path"], captured["key_path"] = cert
            self.assertTrue(os.path.exists(captured["cert_path"]))
            self.assertTrue(os.path.exists(captured["key_path"]))
            return mock.Mock(status_code=200, json=lambda: {"ok": True}, headers={})

        mock_request.side_effect = _fake_request
        _client().call("GET", "/business-account/v1/cuentas")
        self.assertFalse(os.path.exists(captured["cert_path"]))
        self.assertFalse(os.path.exists(captured["key_path"]))

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_removes_temp_cert_files_even_on_transport_error(self, mock_request):
        import requests as requests_module

        captured = {}

        def _fake_request(
            method, url, headers=None, json=None, cert=None, timeout=None
        ):
            captured["cert_path"], captured["key_path"] = cert
            raise requests_module.exceptions.ConnectionError("boom")

        mock_request.side_effect = _fake_request
        with self.assertRaises(ItauApiError):
            _client().call("GET", "/business-account/v1/cuentas")
        self.assertFalse(os.path.exists(captured["cert_path"]))
        self.assertFalse(os.path.exists(captured["key_path"]))

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_returns_parsed_json_on_200(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=200,
            json=lambda: {"cuentas": [{"numero": "123456"}]},
            headers={},
        )
        result = _client().call("GET", "/business-account/v1/cuentas")
        self.assertEqual(result["cuentas"][0]["numero"], "123456")

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_returns_parsed_json_on_201(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=201, json=lambda: {"id": "abc"}, headers={}
        )
        result = _client().call("POST", "/payments-platform/v1/pagos", body={"a": 1})
        self.assertEqual(result["id"], "abc")

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_raises_itau_api_error_on_non_2xx_with_json_body(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=400,
            json=lambda: {"message": "Solicitud inválida"},
            text='{"message": "Solicitud inválida"}',
            headers={},
        )
        with self.assertRaises(ItauApiError) as ctx:
            _client().call("GET", "/business-account/v1/cuentas")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("inválida", ctx.exception.message)

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_raises_itau_api_error_on_non_json_error_body(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=500,
            json=mock.Mock(side_effect=ValueError()),
            text="Internal Server Error",
            headers={},
        )
        with self.assertRaises(ItauApiError) as ctx:
            _client().call("GET", "/business-account/v1/cuentas")
        self.assertEqual(ctx.exception.status_code, 500)
        self.assertIn("Internal Server Error", ctx.exception.message)

    @mock.patch(
        "odoo.addons.l10n_py_account_payment_itau.models.itau_api_client.requests.request"
    )
    def test_call_sends_canal_token_header_only_when_configured(self, mock_request):
        mock_request.return_value = mock.Mock(
            status_code=200, json=lambda: {"ok": True}, headers={}
        )
        _client().call("GET", "/business-account/v1/cuentas")
        _, kwargs_without_token = mock_request.call_args
        self.assertNotIn("X-Itau-Canal-Token", kwargs_without_token["headers"])

        _client(canal_token="test-canal-token").call(
            "GET", "/business-account/v1/cuentas"
        )
        _, kwargs_with_token = mock_request.call_args
        self.assertEqual(
            kwargs_with_token["headers"]["X-Itau-Canal-Token"], "test-canal-token"
        )

    def test_call_with_empty_client_cert_raises_clean_error(self):
        client = ItauApiClient(
            environment_url="https://openbanking.itau.com.py/sandbox",
            client_cert_pem=False,
            client_key_pem=_TEST_KEY_PEM,
        )
        with self.assertRaises(ItauApiError) as ctx:
            client.call("GET", "/business-account/v1/cuentas")
        self.assertIn("certificado mTLS", ctx.exception.message)

    def test_call_with_empty_client_key_raises_clean_error(self):
        client = ItauApiClient(
            environment_url="https://openbanking.itau.com.py/sandbox",
            client_cert_pem=_TEST_CERT_PEM,
            client_key_pem=False,
        )
        with self.assertRaises(ItauApiError) as ctx:
            client.call("GET", "/business-account/v1/cuentas")
        self.assertIn("certificado mTLS", ctx.exception.message)
