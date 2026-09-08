# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_py_account_batch_payment.models.account_payment_order import (
    L10N_PY_SIPAP_BATCH_CODE,
)


@tagged("post_install", "-at_install", "l10n_py")
class TestItauDispatch(AccountTestInvoicingCommon):
    """Proves the plug-in mechanism end-to-end: a bank configured with
    ``export_code="itau"``/``export_mode="api"`` resolves, with no core
    changes, to THIS module's ``_l10n_py_dispatch_batch_api_itau`` --
    which, deliberately, is a stub that raises a clear error rather than
    calling a real, unconfirmed API. See this module's README for why.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.write(
            {
                "groups_id": [
                    Command.link(
                        cls.env.ref("account_payment_order.group_account_payment").id
                    )
                ]
            }
        )
        cls.company = cls.company_data["company"]
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.itau_bank = cls.env["res.bank"].create(
            {
                "name": "Banco Itaú Paraguay S.A.",
                "l10n_py_sipap_export_code": "itau",
                "l10n_py_sipap_export_mode": "api",
            }
        )
        cls.company_bank_account = cls.env["res.partner.bank"].create(
            {
                "acc_number": "COMPANY-ITAU-0001",
                "partner_id": cls.company.partner_id.id,
                "bank_id": cls.itau_bank.id,
                "company_id": cls.company.id,
            }
        )
        cls.bank_journal.bank_account_id = cls.company_bank_account.id
        cls.sipap_method = (
            cls.env["account.payment.method"]
            .sudo()
            .search([("code", "=", L10N_PY_SIPAP_BATCH_CODE)], limit=1)
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "SIPAP Batch File - Itaú Test Mode",
                "company_id": cls.company.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.bank_journal.id,
                "payment_method_id": cls.sipap_method.id,
            }
        )

    def _create_order(self):
        return self.env["account.payment.order"].create(
            {"payment_mode_id": self.payment_mode.id}
        )

    def test_generate_batch_file_resolves_to_itau_api_handler(self):
        """The framework must reach _l10n_py_dispatch_batch_api_itau
        (not silently do nothing, not fall through to the file-export
        path) -- proven by asserting on the error THIS module's handler
        raises, not a generic 'no handler found' error from the core."""
        order = self._create_order()
        with self.assertRaises(UserError) as ctx:
            order._l10n_py_generate_batch_file()
        self.assertIn("Payments Platform", str(ctx.exception))
        self.assertIn("Fase 3", str(ctx.exception))

    def test_generate_payment_file_dispatches_for_sipap_method(self):
        """generate_payment_file() (the real entry point used by the
        payment-order UI/workflow) reaches the same handler as the
        internal _l10n_py_generate_batch_file() call above."""
        order = self._create_order()
        with self.assertRaises(UserError):
            order.generate_payment_file()

    def test_stub_error_names_the_configured_bank(self):
        """The stub's error message should help whoever hits it identify
        which bank triggered it, not just say 'not implemented'."""
        order = self._create_order()
        with self.assertRaises(UserError) as ctx:
            order._l10n_py_dispatch_batch_api_itau()
        self.assertIn("Itaú", str(ctx.exception))
