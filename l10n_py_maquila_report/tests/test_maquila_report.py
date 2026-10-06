# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMaquilaReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.matriz = cls.env["res.partner"].create({"name": "Rep Matriz"})
        cls.program = cls.env["l10n_py.maquila.program"].create(
            {
                "name": "Rep Program",
                "code": "RES-BIM-REP-001",
                "maquila_type": "pura",
                "matriz_partner_id": cls.matriz.id,
                "company_id": cls.company.id,
                "state": "active",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Rep Product", "is_storable": True}
        )
        # one admission and one export in the period
        cls.admission = cls.env["l10n_py.maquila.admission"].create(
            {
                "name": "DI-REP-1",
                "program_id": cls.program.id,
                "cnime_certificate": "CN-REP",
                "amount_cif": 10000,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "quantity": 100,
                            "fob_value": 10000,
                        },
                    )
                ],
            }
        )
        cls.export = cls.env["l10n_py.maquila.export"].create(
            {
                "name": "EXP-REP-1",
                "program_id": cls.program.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "quantity": 80,
                            "fob_value": 15000,
                        },
                    )
                ],
            }
        )
        cls.report = cls.env["l10n_py.maquila.cnime.report"].create(
            {
                "program_id": cls.program.id,
                "period_start": fields.Date.to_date("2026-01-01"),
                "period_end": fields.Date.to_date("2026-12-31"),
                "employment_count": 25,
            }
        )

        # A validated incoming stock move into the maquila location, so
        # stock_balance is populated for the SIMEX payload tests.
        cls.maquila_loc = cls.env.ref("l10n_py_maquila_ops.stock_location_maquila")
        cls.supplier_loc = cls.env.ref("stock.stock_location_suppliers")
        cls.stock_move = cls.env["stock.move"].create(
            {
                "name": "Rep stock in",
                "product_id": cls.product.id,
                "product_uom_qty": 40,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.supplier_loc.id,
                "location_dest_id": cls.maquila_loc.id,
                "company_id": cls.company.id,
                "date": fields.Datetime.to_datetime("2026-06-01"),
            }
        )
        cls.stock_move._action_confirm()
        cls.stock_move._action_assign()
        cls.stock_move.quantity = 40
        cls.stock_move.picked = True
        cls.stock_move._action_done()

        # A user in group_maquila_user (read-only) to test that both
        # actions requiring write access are blocked for it.
        cls.restricted_user = cls.env["res.users"].create(
            {
                "name": "Rep Restricted User",
                "login": "rep_restricted_user",
                "email": "rep_restricted_user@example.com",
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("l10n_py_maquila_base.group_maquila_user").id,
                        ],
                    )
                ],
            }
        )

    def test_display_name(self):
        """The record title names the program and the period, not the
        technical model name and id."""
        self.assertEqual(
            self.report.display_name, "CNIME RES-BIM-REP-001 2026-01 / 2026-12"
        )
        self.report.period_end = fields.Date.to_date("2026-01-31")
        self.assertEqual(self.report.display_name, "CNIME RES-BIM-REP-001 2026-01")

    def test_report_data_populated(self):
        # Data is compiled by action_generate(), not by a compute.
        self.report.action_generate()
        self.assertTrue(self.report.import_data)
        self.assertIn("DI-REP-1", self.report.import_data)
        self.assertTrue(self.report.export_data)
        self.assertIn("EXP-REP-1", self.report.export_data)

    def test_report_state_flow(self):
        self.assertEqual(self.report.state, "draft")
        self.report.action_generate()
        self.assertEqual(self.report.state, "generated")
        self.report.action_validate()
        self.assertEqual(self.report.state, "validated")
        self.report.submission_protocol = "PROT-TEST-001"
        self.report.action_submit()
        self.assertEqual(self.report.state, "submitted")
        self.assertTrue(self.report.submission_date)

    def test_submitted_report_is_frozen(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.submission_protocol = "PROT-TEST-001"
        self.report.action_submit()
        # A submitted report cannot be reset to draft nor regenerated.
        with self.assertRaises(UserError):
            self.report.action_draft()
        with self.assertRaises(UserError):
            self.report.action_generate()

    def test_simex_payload(self):
        self.report.action_generate()
        result = self.report.action_generate_simex_payload()
        self.assertEqual(result["type"], "ir.actions.client")

    def test_submit_requires_protocol(self):
        self.report.action_generate()
        self.report.action_validate()
        self.assertFalse(self.report.submission_protocol)
        with self.assertRaises(UserError):
            self.report.action_submit()
        self.assertEqual(self.report.state, "validated")
        self.assertFalse(self.report.submission_date)
        self.report.submission_protocol = "PROT-TEST-001"
        self.report.action_submit()
        self.assertEqual(self.report.state, "submitted")
        self.assertTrue(self.report.submission_date)

    def _simex_attachments(self):
        return self.env["ir.attachment"].search(
            [
                ("res_model", "=", "l10n_py.maquila.cnime.report"),
                ("res_id", "=", self.report.id),
                ("name", "=like", "simex_%"),
            ]
        )

    def test_simex_payload_two_attachments(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.action_generate_simex_payload()
        attachments = self._simex_attachments()
        self.assertEqual(len(attachments), 2)
        self.assertTrue(all(att.mimetype == "application/json" for att in attachments))
        names = attachments.mapped("name")
        self.assertTrue(any("cuenta_corriente" in name for name in names))
        self.assertTrue(any("inversion_empleo" in name for name in names))

    def test_simex_payload_groups(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.action_generate_simex_payload()
        attachments = self._simex_attachments()
        payloads = {}
        for att in attachments:
            key = (
                "cuenta_corriente"
                if "cuenta_corriente" in att.name
                else "inversion_empleo"
            )
            payloads[key] = json.loads(base64.b64decode(att.datas))

        cuenta_corriente = payloads["cuenta_corriente"]
        self.assertEqual(
            set(cuenta_corriente.keys()),
            {
                "programa",
                "periodo_inicio",
                "periodo_fin",
                "importaciones",
                "exportaciones",
                "produccion",
                "consumo",
                "residuos",
                "stock_balance",
            },
        )
        self.assertTrue(cuenta_corriente["stock_balance"])
        self.assertEqual(
            cuenta_corriente["stock_balance"],
            json.loads(self.report.stock_balance),
        )
        self.assertEqual(cuenta_corriente["stock_balance"][0]["product"], "Rep Product")
        self.assertEqual(cuenta_corriente["stock_balance"][0]["quantity"], 40)

        inversion_empleo = payloads["inversion_empleo"]
        self.assertEqual(
            set(inversion_empleo.keys()),
            {"programa", "periodo_inicio", "periodo_fin", "van_total", "empleo"},
        )

    def test_simex_payload_chatter_summary(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.action_generate_simex_payload()
        attachments = self._simex_attachments()
        message = self.report.message_ids.sorted("id", reverse=True)[0]
        self.assertNotIn("importaciones", message.body or "")
        self.assertIn("2", message.body or "")
        self.assertEqual(set(message.attachment_ids.ids), set(attachments.ids))

    def test_simex_payload_regenerate_replaces(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.action_generate_simex_payload()
        first_ids = set(self._simex_attachments().ids)
        self.report.action_generate_simex_payload()
        second_ids = set(self._simex_attachments().ids)
        self.assertEqual(len(second_ids), 2)
        self.assertFalse(first_ids & second_ids)

    def test_simex_payload_blocked_when_submitted(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.action_generate_simex_payload()
        before_ids = set(self._simex_attachments().ids)
        self.report.submission_protocol = "PROT-TEST-001"
        self.report.action_submit()
        with self.assertRaises(UserError):
            self.report.action_generate_simex_payload()
        after_ids = set(self._simex_attachments().ids)
        self.assertEqual(before_ids, after_ids)

    def test_simex_payload_and_submit_blocked_for_user(self):
        self.report.action_generate()
        self.report.action_validate()
        self.report.submission_protocol = "PROT-TEST-001"
        report_as_user = self.report.with_user(self.restricted_user)
        with self.assertRaises(AccessError):
            report_as_user.action_generate_simex_payload()
        self.assertFalse(self._simex_attachments())
        with self.assertRaises(AccessError):
            report_as_user.action_submit()
        self.assertEqual(self.report.state, "validated")

    def test_account_move_legend(self):
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.matriz.id,
                "l10n_py_maquila_program_id": self.program.id,
            }
        )
        self.assertTrue(move.l10n_py_is_maquila_export)
        # The SIFEN legend method must inject the maquila legend.
        data = move._prepare_edi_document_data()
        self.assertIn("Ley 7547/2025", data.get("observacion") or "")
