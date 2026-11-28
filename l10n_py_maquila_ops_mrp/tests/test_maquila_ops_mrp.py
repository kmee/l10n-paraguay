# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMaquilaOpsMrp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # A valid "timbrado" (SET authorization) is required to post a sale
        # invoice under l10n_py_account. Set one up the same way
        # l10n_py_account/tests/test_account_move.py does.
        cls.doc_type_invoice = cls.env["l10n_latam.document.type"].search(
            [("country_id", "=", cls.env.ref("base.py").id), ("code", "=", "1")],
            limit=1,
        )
        if not cls.doc_type_invoice:
            cls.doc_type_invoice = cls.env["l10n_latam.document.type"].create(
                {
                    "name": "Factura",
                    "code": "1",
                    "country_id": cls.env.ref("base.py").id,
                    "internal_type": "invoice",
                }
            )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Ventas Bridge Test",
                "type": "sale",
                "code": "VBT",
                "company_id": cls.company.id,
                "l10n_latam_use_documents": True,
            }
        )
        today = date.today()
        cls.authorization = cls.env["account.authorization"].create(
            {
                "name": "22334455",
                "date_from": today - timedelta(days=30),
                "date_to": today + timedelta(days=335),
                "invoice_number_from": 1,
                "invoice_number_to": 10000,
                "establishment": "001",
                "expedition_point": "001",
                "l10n_latam_document_type_id": cls.doc_type_invoice.id,
                "company_id": cls.company.id,
            }
        )

        cls.matriz = cls.env["res.partner"].create({"name": "Bridge Matriz"})
        cls.program = cls.env["l10n_py.maquila.program"].create(
            {
                "name": "Bridge Program",
                "code": "RES-BIM-BRG-001",
                "maquila_type": "pura",
                "matriz_partner_id": cls.matriz.id,
                "company_id": cls.company.id,
                "state": "active",
            }
        )
        cls.plan = cls.env["account.analytic.plan"].search([], limit=1) or cls.env[
            "account.analytic.plan"
        ].create({"name": "Bridge plan"})
        cls.analytic = cls.env["account.analytic.account"].create(
            {"name": "Bridge analytic", "plan_id": cls.plan.id}
        )
        cls.categ = cls.env["product.category"].create(
            {"name": "Bridge Std", "property_cost_method": "standard"}
        )
        cls.finished = cls.env["product.product"].create(
            {
                "name": "Bridge Finished",
                "is_storable": True,
                "categ_id": cls.categ.id,
            }
        )
        cls.raw_ta = cls.env["product.product"].create(
            {
                "name": "Bridge Raw TA",
                "is_storable": True,
                "standard_price": 10,
                "categ_id": cls.categ.id,
            }
        )
        cls.raw_nat = cls.env["product.product"].create(
            {
                "name": "Bridge Raw National",
                "is_storable": True,
                "standard_price": 20,
                "categ_id": cls.categ.id,
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1,
                "l10n_py_maquila_program_id": cls.program.id,
                "l10n_py_intn_certified": True,
                "l10n_py_intn_certificate": "INTN-BRIDGE-1",
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.raw_ta.id,
                            "product_qty": 2,
                            "l10n_py_origin_type": "temporary_admission",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.raw_nat.id,
                            "product_qty": 3,
                            "l10n_py_origin_type": "national_py",
                        },
                    ),
                ],
            }
        )
        cls.export_product = cls.env["product.product"].create(
            {"name": "Bridge Export Product", "is_storable": False}
        )

    def _make_done_production(self):
        mo_form = Form(self.env["mrp.production"])
        mo_form.product_id = self.finished
        mo_form.bom_id = self.bom
        mo_form.product_qty = 1.0
        mo = mo_form.save()
        mo.action_confirm()
        mo_form = Form(mo)
        mo_form.qty_producing = 1.0
        mo = mo_form.save()
        mo.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
        return mo

    def _make_export_invoice(self, amount, invoice_date="2026-06-15"):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.matriz.id,
                "invoice_date": invoice_date,
                "journal_id": self.journal.id,
                "l10n_py_authorization_id": self.authorization.id,
                "l10n_py_maquila_program_id": self.program.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.export_product.id,
                            "quantity": 1,
                            "price_unit": amount,
                            "tax_ids": False,
                        },
                    )
                ],
            }
        )
        move.action_post()
        return move

    def _make_tum_wizard(self):
        return self.env["l10n_py.maquila.tum.wizard"].create(
            {
                "program_id": self.program.id,
                "period_start": "2026-01-01",
                "period_end": "2026-12-31",
            }
        )

    def test_action_compute_requires_analytic(self):
        wiz = self._make_tum_wizard()
        with self.assertRaises(UserError):
            wiz.action_compute()

    def test_action_compute_no_production_falls_back_to_export_invoice(self):
        self.program.analytic_account_id = self.analytic.id
        self._make_export_invoice(5000)
        wiz = self._make_tum_wizard()
        wiz.action_compute()
        self.assertEqual(wiz.van_amount, 0)
        self.assertEqual(wiz.total_cost, 0)
        self.assertTrue(wiz.van_warning)
        self.assertEqual(wiz.export_invoice_amount, 5000)
        self.assertEqual(wiz.tum_base, wiz.export_invoice_amount)

    def test_action_compute_with_production_van_above_export(self):
        self.program.analytic_account_id = self.analytic.id
        self.env["account.analytic.line"].create(
            {
                "name": "total cost",
                "account_id": self.analytic.id,
                "amount": -8000,
                "date": "2026-06-01",
            }
        )
        self._make_done_production()
        self._make_export_invoice(5000)
        wiz = self._make_tum_wizard()
        wiz.currency_id = self.company.currency_id.id
        wiz.action_compute()
        self.assertFalse(wiz.van_warning)
        self.assertEqual(wiz.total_cost, 8000)
        self.assertEqual(wiz.imported_cost, 20)
        self.assertEqual(wiz.national_cost, 60)
        self.assertEqual(wiz.van_amount, 7980)
        self.assertEqual(wiz.tum_base, wiz.van_amount)
        self.assertEqual(
            wiz.tum_amount,
            wiz.currency_id.round(wiz.tum_base * wiz.tum_rate / 100),
        )

    def test_action_compute_export_above_van(self):
        self.program.analytic_account_id = self.analytic.id
        self.env["account.analytic.line"].create(
            {
                "name": "total cost",
                "account_id": self.analytic.id,
                "amount": -8000,
                "date": "2026-06-01",
            }
        )
        self._make_done_production()
        self._make_export_invoice(10000)
        wiz = self._make_tum_wizard()
        wiz.currency_id = self.company.currency_id.id
        wiz.action_compute()
        self.assertEqual(wiz.van_amount, 7980)
        self.assertEqual(wiz.tum_base, wiz.export_invoice_amount)

    def test_action_compute_converts_to_wizard_currency(self):
        self.program.analytic_account_id = self.analytic.id
        self.env["account.analytic.line"].create(
            {
                "name": "total cost",
                "account_id": self.analytic.id,
                "amount": -8000,
                "date": "2026-06-01",
            }
        )
        self._make_done_production()
        usd = self.env.ref("base.USD")
        eur = self.env.ref("base.EUR")
        wizard_currency = eur if self.company.currency_id == usd else usd
        wizard_currency.active = True
        wiz = self._make_tum_wizard()
        wiz.currency_id = wizard_currency.id
        self.env["res.currency.rate"].create(
            {
                "currency_id": wizard_currency.id,
                "rate": 7300.0,
                "name": wiz.period_end,
                "company_id": self.company.id,
            }
        )
        wiz.action_compute()
        expected = self.company.currency_id._convert(
            7980, wizard_currency, self.company, wiz.period_end
        )
        self.assertEqual(wiz.van_amount, expected)
        self.assertNotEqual(wiz.van_amount, 7980)
