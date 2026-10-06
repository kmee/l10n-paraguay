# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import timedelta

from odoo import Command, fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install", "l10n_py")
class TestAccountMoveExchangeRate(TransactionCase):
    """Exchange rate to PYG of foreign currency invoices (SIFEN dTiCam)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        country_py = cls.env.ref("base.py")
        currency_pyg = cls.env.ref("base.PYG")
        currency_pyg.active = True
        cls.usd = cls.env.ref("base.USD")
        cls.usd.active = True
        company = cls.env["res.company"].create(
            {
                "name": "Tipo de Cambio Test SA",
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
        cls.today = fields.Date.context_today(cls.env["account.move"])
        cls.env["account.authorization"].create(
            {
                "name": "20000001",
                "date_from": cls.today - timedelta(days=30),
                "date_to": cls.today + timedelta(days=335),
                "invoice_number_from": 1,
                "invoice_number_to": 10000,
                "establishment": "001",
                "expedition_point": "001",
                "l10n_latam_document_type_id": cls.env.ref(
                    "l10n_py_account.dc_py_f"
                ).id,
                "company_id": cls.company.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Cliente del Exterior", "country_id": cls.env.ref("base.br").id}
        )
        # rate = USD per 1 PYG (company currency)
        cls.env["res.currency.rate"].create(
            [
                {
                    "currency_id": cls.usd.id,
                    "company_id": cls.company.id,
                    "name": cls.today - timedelta(days=10),
                    "rate": 1 / 7000.0,
                },
                {
                    "currency_id": cls.usd.id,
                    "company_id": cls.company.id,
                    "name": cls.today,
                    "rate": 1 / 7350.0,
                },
            ]
        )

    def _create_invoice(self, **vals):
        """Plain create() values, as sale.order._create_invoices does"""
        return self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal.id,
                "currency_id": self.usd.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Perfil",
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
                **vals,
            }
        )

    def test_rate_from_currency_at_invoice_date(self):
        invoice = self._create_invoice(invoice_date=self.today)
        self.assertAlmostEqual(invoice.l10n_py_exchange_rate, 7350.0, places=4)
        self.assertAlmostEqual(invoice.l10n_py_amount_total_pyg, 7350000.0, places=0)

    def test_rate_follows_invoice_date(self):
        invoice = self._create_invoice(invoice_date=self.today)
        invoice.invoice_date = self.today - timedelta(days=5)
        self.assertAlmostEqual(invoice.l10n_py_exchange_rate, 7000.0, places=4)

    def test_invoice_created_from_order_without_date(self):
        """Invoice from a sale order: no date and no rate in the values; the
        rate is there before and after posting"""
        invoice = self._create_invoice()
        self.assertAlmostEqual(invoice.l10n_py_exchange_rate, 7350.0, places=4)
        invoice.action_post()
        self.assertEqual(invoice.state, "posted")
        self.assertAlmostEqual(invoice.l10n_py_exchange_rate, 7350.0, places=4)

    def test_manual_rate_is_kept_and_booked(self):
        invoice = self._create_invoice(invoice_date=self.today)
        invoice.l10n_py_exchange_rate = 7400.0
        self.assertAlmostEqual(invoice.invoice_currency_rate, 1 / 7400.0)
        invoice.action_post()
        self.assertAlmostEqual(invoice.l10n_py_exchange_rate, 7400.0, places=4)
        receivable = invoice.line_ids.filtered(
            lambda line: line.account_id.account_type == "asset_receivable"
        )
        self.assertAlmostEqual(receivable.balance, 7400000.0, places=0)

    def test_manual_rate_at_create_is_kept(self):
        invoice = self._create_invoice(
            invoice_date=self.today, l10n_py_exchange_rate=7380.0
        )
        self.assertAlmostEqual(invoice.l10n_py_exchange_rate, 7380.0, places=4)
        self.assertAlmostEqual(invoice.invoice_currency_rate, 1 / 7380.0)

    def test_pyg_invoice_has_no_rate(self):
        invoice = self._create_invoice(
            invoice_date=self.today, currency_id=self.company.currency_id.id
        )
        self.assertFalse(invoice.l10n_py_exchange_rate)
