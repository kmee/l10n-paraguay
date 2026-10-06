# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestAccountMoveTimbrado(TransactionCase):
    """Timbrado of documents created without one"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        country_py = cls.env.ref("base.py")
        currency_pyg = cls.env.ref("base.PYG")
        currency_pyg.active = True
        company = cls.env["res.company"].create(
            {
                "name": "Timbrado Test SA",
                "country_id": country_py.id,
                "account_fiscal_country_id": country_py.id,
                "currency_id": currency_pyg.id,
            }
        )
        cls.env.user.company_ids |= company
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[company.id])
        )
        cls.company = cls.env["res.company"].browse(company.id)
        cls.env["account.chart.template"].try_loading(
            "py", cls.company, install_demo=False
        )
        cls.journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "sale")], limit=1
        )
        cls.journal.write(
            {
                "l10n_latam_use_documents": True,
                "l10n_py_establishment": "001",
                "l10n_py_point": "001",
            }
        )
        cls.doc_invoice = cls.env.ref("l10n_py_account.dc_py_f")
        cls.doc_credit_note = cls.env.ref("l10n_py_account.dc_py_nc")
        cls.partner = cls.env["res.partner"].create(
            {"name": "Cliente Timbrado", "country_id": country_py.id}
        )
        cls.today = fields.Date.context_today(cls.env["account.move"])
        cls.auth_001 = cls._create_authorization("10000001")
        # Same document type, other expedition point of the same company
        cls.auth_002 = cls._create_authorization("10000002", expedition_point="002")
        cls.auth_nc = cls._create_authorization(
            "10000003", document_type=cls.doc_credit_note
        )

    @classmethod
    def _create_authorization(
        cls, name, expedition_point="001", document_type=None, **vals
    ):
        return cls.env["account.authorization"].create(
            {
                "name": name,
                "date_from": cls.today - timedelta(days=30),
                "date_to": cls.today + timedelta(days=335),
                "invoice_number_from": 1,
                "invoice_number_to": 10000,
                "establishment": "001",
                "expedition_point": expedition_point,
                "l10n_latam_document_type_id": (document_type or cls.doc_invoice).id,
                "company_id": cls.company.id,
                **vals,
            }
        )

    def _create_move(self, move_type="out_invoice", **vals):
        """Create a document the way sale.order._create_invoices does: plain
        create() values, no onchange and no timbrado."""
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "invoice_date": self.today,
                "invoice_line_ids": [
                    Command.create(
                        {"name": "Servicio", "quantity": 1, "price_unit": 110000}
                    )
                ],
                **vals,
            }
        )

    # ============== Timbrado of the document ==============

    def test_timbrado_from_journal_point(self):
        """Two valid invoice timbrados in the company: the one of the journal
        establishment and expedition point is used"""
        invoice = self._create_move()
        self.assertEqual(invoice.l10n_latam_document_type_id, self.doc_invoice)
        self.assertEqual(invoice.l10n_py_authorization_id, self.auth_001)
        invoice.action_post()
        self.assertEqual(invoice.l10n_py_authorization_id, self.auth_001)
        self.assertEqual(invoice.l10n_py_invoice_number, 1)

    def test_timbrado_of_journal_has_priority(self):
        """The timbrado set on the journal wins over other fitting ones"""
        auth_bis = self._create_authorization("10000004")
        self.journal.l10n_py_authorization_id = auth_bis
        invoice = self._create_move()
        self.assertEqual(invoice.l10n_py_authorization_id, auth_bis)

    def test_ambiguous_timbrado_is_not_guessed(self):
        """Two fitting timbrados for the same point: no choice is made, the
        user is warned and posting asks for the timbrado"""
        self._create_authorization("10000004")
        invoice = self._create_move()
        self.assertFalse(invoice.l10n_py_authorization_id)
        warning = invoice._onchange_l10n_py_authorization_ambiguous()
        self.assertIn("More than one timbrado", warning["warning"]["message"])
        with self.assertRaises(UserError):
            invoice.action_post()

    def test_timbrado_valid_on_invoice_date(self):
        """A timbrado is only proposed for dates inside its validity"""
        invoice = self._create_move(invoice_date=self.today - timedelta(days=60))
        self.assertFalse(invoice.l10n_py_authorization_id)
        invoice.invoice_date = self.today
        self.assertEqual(invoice.l10n_py_authorization_id, self.auth_001)

    def test_manual_timbrado_is_kept(self):
        """A timbrado chosen by the user stays while it fits the document"""
        invoice = self._create_move(l10n_py_authorization_id=self.auth_002.id)
        invoice.invoice_date = self.today - timedelta(days=1)
        self.assertEqual(invoice.l10n_py_authorization_id, self.auth_002)

    def test_credit_note_timbrado(self):
        """A credit note gets the credit note timbrado of the point"""
        credit_note = self._create_move(move_type="out_refund")
        self.assertEqual(credit_note.l10n_latam_document_type_id, self.doc_credit_note)
        self.assertEqual(credit_note.l10n_py_authorization_id, self.auth_nc)

    def test_vendor_bill_untouched(self):
        """Vendor bills are not numbered by an own timbrado"""
        purchase_journal = self.env["account.journal"].search(
            [("company_id", "=", self.company.id), ("type", "=", "purchase")],
            limit=1,
        )
        bill = self._create_move(
            move_type="in_invoice",
            journal_id=purchase_journal.id,
            l10n_latam_document_number="001-001-0000123",
        )
        self.assertFalse(bill.l10n_py_authorization_id)
