# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from unittest import mock

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.account_payment_batch_oca.models.account_payment_order import (
    AccountPaymentOrder,
)

from ..models.account_payment_order import L10N_PY_SIPAP_BATCH_CODE


@tagged("post_install", "-at_install", "l10n_py")
class TestBatchFileDispatch(AccountTestInvoicingCommon):
    """Tests for the pluggable SIPAP batch-file exporter framework.

    This module implements no concrete bank layout: it only resolves,
    from ``res.bank.l10n_py_sipap_export_code``, which
    ``_l10n_py_generate_batch_file_<code>`` method (registered by an
    exporter module, e.g. ``l10n_py_account_batch_payment_iso20022``)
    should generate the file. These tests exercise only that dispatch
    mechanism: they never fabricate a real bank file format.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write(
            {
                "groups_id": [
                    Command.link(
                        cls.env.ref(
                            "account_payment_batch_oca.group_account_payment"
                        ).id
                    )
                ]
            }
        )
        cls.company = cls.company_data["company"]
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.company_bank = cls.env["res.bank"].create({"name": "Test Company Bank"})
        cls.company_bank_account = cls.env["res.partner.bank"].create(
            {
                "acc_number": "COMPANY-DISPATCH-0001",
                "partner_id": cls.company.partner_id.id,
                "bank_id": cls.company_bank.id,
                "company_id": cls.company.id,
            }
        )
        cls.bank_journal.bank_account_id = cls.company_bank_account.id
        cls.sipap_method = (
            cls.env["account.payment.method"]
            .sudo()
            .search([("code", "=", L10N_PY_SIPAP_BATCH_CODE)], limit=1)
        )
        cls.method_line = cls.env["account.payment.method.line"].create(
            {
                "name": "SIPAP Batch File - Test",
                "company_id": cls.company.id,
                "journal_id": cls.bank_journal.id,
                "payment_method_id": cls.sipap_method.id,
                "selectable": True,
            }
        )

    def _create_order(self):
        return self.env["account.payment.order"].create(
            {
                "payment_type": "outbound",
                "payment_method_line_id": self.method_line.id,
            }
        )

    def test_payment_method_is_registered(self):
        """The 'SIPAP Batch File' payment method is installed by data file."""
        self.assertTrue(self.sipap_method)
        self.assertEqual(self.sipap_method.payment_type, "outbound")
        self.assertTrue(self.sipap_method.payment_order_ok)
        self.assertTrue(self.sipap_method.bank_account_required)

    def test_missing_bank_on_company_account_raises_clear_error(self):
        """No bank on the company bank account -> explicit UserError."""
        order = self._create_order()
        self.assertTrue(order.company_partner_bank_id)
        order.company_partner_bank_id.bank_id = False
        with self.assertRaises(UserError):
            order._l10n_py_generate_batch_file()

    def test_missing_export_code_raises_clear_error(self):
        """Bank without l10n_py_sipap_export_code configured -> UserError."""
        order = self._create_order()
        bank = order.company_partner_bank_id.bank_id
        self.assertTrue(bank)
        bank.l10n_py_sipap_export_code = False
        with self.assertRaises(UserError):
            order._l10n_py_generate_batch_file()

    def test_unregistered_export_code_raises_clear_error(self):
        """A configured export code with no matching handler -> UserError."""
        order = self._create_order()
        bank = order.company_partner_bank_id.bank_id
        bank.l10n_py_sipap_export_code = "no_such_exporter_installed"
        with self.assertRaises(UserError):
            order._l10n_py_generate_batch_file()

    def test_dispatches_to_the_registered_handler(self):
        """When a matching '_l10n_py_generate_batch_file_<code>' handler is
        registered on account.payment.order, the framework calls exactly
        that handler -- this is the mechanism a real exporter module (e.g.
        the ISO 20022 one) relies on, tested here without depending on
        any concrete exporter module being installed."""
        order = self._create_order()
        bank = order.company_partner_bank_id.bank_id
        bank.l10n_py_sipap_export_code = "dummy_test_format"

        sentinel = object()
        with mock.patch.object(
            AccountPaymentOrder,
            "_l10n_py_generate_batch_file_dummy_test_format",
            create=True,
            return_value=sentinel,
        ) as handler:
            result = order._l10n_py_generate_batch_file()
        handler.assert_called_once()
        self.assertIs(result, sentinel)

    def test_generate_payment_file_dispatches_for_sipap_method(self):
        """generate_payment_file() delegates to the SIPAP framework only
        when the order's payment method is the SIPAP batch method."""
        order = self._create_order()
        bank = order.company_partner_bank_id.bank_id
        bank.l10n_py_sipap_export_code = "dummy_test_format"

        with mock.patch.object(
            AccountPaymentOrder,
            "_l10n_py_generate_batch_file_dummy_test_format",
            create=True,
            return_value=(False, False),
        ) as handler:
            order.generate_payment_file()
        handler.assert_called_once()
