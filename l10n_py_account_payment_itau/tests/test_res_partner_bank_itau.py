# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import base64

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_py_account_payment_itau.models.itau_api_client import (
    ItauApiClient,
)

_TEST_CERT_B64 = base64.b64encode(b"test-cert").decode()
_TEST_KEY_B64 = base64.b64encode(b"test-key").decode()


@tagged("post_install", "-at_install", "l10n_py")
class TestItauApiClientFromBankAccount(TransactionCase):
    """from_bank_account() must raise a clear UserError for every
    misconfiguration, mirroring the discipline already established by
    AtlasApiClient.from_bank_account (same repo, sibling module)."""

    def setUp(self):
        super().setUp()
        self.env.user.groups_id |= self.env.ref(
            "account_payment_order.group_account_payment"
        )
        self.partner = self.env["res.partner"].create({"name": "Itaú Test Partner"})

    def _bank_account(self, **values):
        defaults = {
            "acc_number": "ITAU-TEST-0001",
            "partner_id": self.partner.id,
        }
        defaults.update(values)
        return self.env["res.partner.bank"].create(defaults)

    def test_not_itau_enabled_raises_clear_user_error(self):
        bank_account = self._bank_account()
        with self.assertRaises(UserError):
            ItauApiClient.from_bank_account(bank_account)

    def test_empty_recordset_raises_clear_user_error(self):
        empty = self.env["res.partner.bank"].browse()
        with self.assertRaises(UserError):
            ItauApiClient.from_bank_account(empty)

    def test_missing_cert_or_key_raises_clear_user_error(self):
        bank_account = self._bank_account(
            itau_enabled=True,
            itau_environment="testing",
            itau_production_url="https://openbanking.itau.com.py/sandbox",
        )
        with self.assertRaises(UserError):
            ItauApiClient.from_bank_account(bank_account)

    def test_production_without_url_raises_clear_user_error(self):
        bank_account = self._bank_account(
            itau_enabled=True,
            itau_environment="production",
            itau_production_url=False,
            itau_client_cert=_TEST_CERT_B64,
            itau_client_key=_TEST_KEY_B64,
        )
        with self.assertRaises(UserError):
            ItauApiClient.from_bank_account(bank_account)

    def test_testing_without_url_raises_clear_user_error(self):
        # Unlike Banco Atlas, Itaú has no known public sandbox URL --
        # "testing" must not silently fall back to a guessed default.
        bank_account = self._bank_account(
            itau_enabled=True,
            itau_environment="testing",
            itau_production_url=False,
            itau_client_cert=_TEST_CERT_B64,
            itau_client_key=_TEST_KEY_B64,
        )
        with self.assertRaises(UserError):
            ItauApiClient.from_bank_account(bank_account)

    def test_fully_configured_builds_client(self):
        bank_account = self._bank_account(
            itau_enabled=True,
            itau_environment="testing",
            itau_production_url="https://openbanking.itau.com.py/sandbox",
            itau_ruc_empresa="80012345-6",
            itau_codigo_empresa="123456",
            itau_client_cert=_TEST_CERT_B64,
            itau_client_key=_TEST_KEY_B64,
        )
        client = ItauApiClient.from_bank_account(bank_account)
        self.assertEqual(
            client.environment_url, "https://openbanking.itau.com.py/sandbox"
        )
        self.assertEqual(client.ruc_empresa, "80012345-6")
