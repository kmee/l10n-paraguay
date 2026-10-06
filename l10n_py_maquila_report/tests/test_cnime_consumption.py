# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCnimeConsumption(TransactionCase):
    """Decreto 5714/2026 Art. 15: the system records the raw material used per
    product (b) and the waste (c, d), consistent with the production."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        matriz = cls.env["res.partner"].create({"name": "Cons Matriz"})
        cls.program = cls.env["l10n_py.maquila.program"].create(
            {
                "name": "Cons Program",
                "code": "RES-BIM-CONS-001",
                "maquila_type": "pura",
                "matriz_partner_id": matriz.id,
                "company_id": cls.company.id,
                "state": "active",
            }
        )
        product = cls.env["product.product"]
        cls.finished = product.create({"name": "Cons Fleje", "is_storable": True})
        cls.coil = product.create({"name": "Cons Bobina", "is_storable": True})
        cls.pack = product.create({"name": "Cons Embalaje", "is_storable": True})
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished.product_tmpl_id.id,
                "product_qty": 1,
                "l10n_py_maquila_program_id": cls.program.id,
                "bom_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.coil.id,
                            "product_qty": 2,
                            "l10n_py_origin_type": "temporary_admission",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": cls.pack.id,
                            "product_qty": 1,
                            "l10n_py_origin_type": "national_py",
                        },
                    ),
                ],
            }
        )

    def _done_production(self, qty, coil_used):
        form = Form(self.env["mrp.production"])
        form.product_id = self.finished
        form.bom_id = self.bom
        form.product_qty = qty
        mo = form.save()
        mo.l10n_py_maquila_program_id = self.program
        mo.action_confirm()
        form = Form(mo)
        form.qty_producing = qty
        mo = form.save()
        coil_move = mo.move_raw_ids.filtered(lambda m: m.product_id == self.coil)
        coil_move.quantity = coil_used
        coil_move.picked = True
        mo.with_context(skip_consumption=True, skip_backorder=True).button_mark_done()
        self.assertEqual(mo.state, "done")
        return mo

    def test_consumption_against_bom_and_waste(self):
        mo = self._done_production(5, coil_used=11)
        self.env["l10n_py.maquila.waste"].create(
            {
                "program_id": self.program.id,
                "production_id": mo.id,
                "product_id": self.coil.id,
                "quantity": 1,
                "waste_type": "scrap",
                "destination": "destruction",
            }
        )
        # A wide period, so the test does not depend on the day it runs.
        today = fields.Date.today()
        report = self.env["l10n_py.maquila.cnime.report"].create(
            {
                "program_id": self.program.id,
                "period_start": today - relativedelta(months=1, day=1),
                "period_end": today + relativedelta(months=1, day=31),
            }
        )
        report.action_generate()
        production = json.loads(report.production_data)
        self.assertEqual(production[0]["quantity"], 5)
        consumption = {c["product"]: c for c in json.loads(report.consumption_data)}
        coil = consumption["Cons Bobina"]
        self.assertEqual(coil["consumed"], 11)
        self.assertEqual(coil["bom_quantity"], 10)
        self.assertEqual(coil["origin"], "temporary_admission")
        self.assertEqual(coil["waste_quantity"], 1)
        self.assertEqual(coil["waste_pct"], round(100 / 11, 2))
        pack = consumption["Cons Embalaje"]
        self.assertEqual(pack["consumed"], 5)
        self.assertEqual(pack["bom_quantity"], 5)
        self.assertEqual(pack["origin"], "national_py")
        self.assertEqual(pack["waste_quantity"], 0)
        report.action_validate()
        report.action_generate_simex_payload()
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", report._name),
                ("res_id", "=", report.id),
                ("name", "=like", "simex_cuenta_corriente_%"),
            ]
        )
        payload = json.loads(attachment.raw)
        self.assertEqual(len(payload["consumo"]), 2)
