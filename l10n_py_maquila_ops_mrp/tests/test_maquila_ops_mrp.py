# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMaquilaOpsMrp(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
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
        # With the Paraguayan localization installed (as when the whole
        # repository is tested) a sale journal of a PY company requires a
        # timbrado; the export invoice here only feeds the TUM amounts.
        cls.sale_journal = cls.env["account.journal"].create(
            {"name": "Bridge Sales", "code": "BRGS", "type": "sale"}
        )
        if "l10n_latam_use_documents" in cls.sale_journal._fields:
            cls.sale_journal.l10n_latam_use_documents = False

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
                "journal_id": self.sale_journal.id,
                "partner_id": self.matriz.id,
                "invoice_date": invoice_date,
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
                # Amounts below are in company currency (PYG when the
                # Paraguayan chart is loaded, USD otherwise).
                "currency_id": self.company.currency_id.id,
            }
        )

    def _cost_line(self):
        # Analytic cost without a journal item: it feeds the MRP split only,
        # it is not value added under Ley 7547/2025 Art. 37.
        self.env["account.analytic.line"].create(
            {
                "name": "total cost",
                "account_id": self.analytic.id,
                "amount": -8000,
                "date": "2026-06-01",
            }
        )

    def test_action_compute_without_analytic_is_informative(self):
        self._make_export_invoice(5000)
        wiz = self._make_tum_wizard()
        wiz.action_compute()
        self.assertTrue(wiz.van_warning)
        self.assertEqual(wiz.total_cost, 0)
        self.assertEqual(wiz.export_invoice_amount, 5000)
        self.assertEqual(wiz.tum_base, 5000)

    def test_action_compute_no_production(self):
        self.program.analytic_account_id = self.analytic.id
        self._cost_line()
        self._make_export_invoice(5000)
        wiz = self._make_tum_wizard()
        wiz.action_compute()
        self.assertTrue(wiz.van_warning)
        self.assertEqual(wiz.total_cost, 0)
        self.assertEqual(wiz.mrp_van_amount, 0)
        self.assertEqual(wiz.van_amount, 0)
        self.assertEqual(wiz.tum_base, wiz.export_invoice_amount)

    def test_action_compute_with_production_does_not_change_base(self):
        self.program.analytic_account_id = self.analytic.id
        self._cost_line()
        self._make_done_production()
        self._make_export_invoice(5000)
        wiz = self._make_tum_wizard()
        wiz.action_compute()
        self.assertFalse(wiz.van_warning)
        self.assertEqual(wiz.total_cost, 8000)
        self.assertEqual(wiz.imported_cost, 20)
        self.assertEqual(wiz.national_cost, 60)
        self.assertEqual(wiz.mrp_van_amount, 7980)
        # The TUM base is the Art. 37 value added (nothing booked here) or the
        # export invoice value, never the MRP national content.
        self.assertEqual(wiz.van_amount, 0)
        self.assertEqual(wiz.tum_base, 5000)
        self.assertEqual(wiz.tum_amount, 50)

    def test_action_compute_converts_to_wizard_currency(self):
        self.program.analytic_account_id = self.analytic.id
        self._cost_line()
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
        self.assertEqual(wiz.mrp_van_amount, expected)
        self.assertNotEqual(wiz.mrp_van_amount, 7980)
