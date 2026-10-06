# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaquilaCnimeReport(models.Model):
    _name = "l10n_py.maquila.cnime.report"
    _description = "CNIME Periodic Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "period_start desc"

    program_id = fields.Many2one(
        "l10n_py.maquila.program",
        required=True,
        tracking=True,
    )
    period_start = fields.Date(required=True, tracking=True)
    period_end = fields.Date(required=True, tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("generated", "Generated"),
            ("validated", "Validated"),
            ("submitted", "Submitted"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )
    # Snapshot fields, filled by action_generate() and frozen afterwards
    # (a periodic report must not silently recompute after submission).
    import_data = fields.Text(readonly=True)
    export_data = fields.Text(readonly=True)
    production_data = fields.Text(readonly=True)
    consumption_data = fields.Text(
        readonly=True,
        help="Raw material used per product (Decreto 5714/2026 Art. 15 b): "
        "quantity consumed by the completed manufacturing orders of the period "
        "against the bill of materials, and the waste recorded for it.",
    )
    waste_data = fields.Text(readonly=True)
    stock_balance = fields.Text(readonly=True)
    employment_count = fields.Integer()
    van_total = fields.Monetary(string="VAN Total", readonly=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.ref("base.USD"),
    )
    submission_date = fields.Datetime(tracking=True)
    submission_protocol = fields.Char(tracking=True)
    company_id = fields.Many2one(
        related="program_id.company_id",
        store=True,
    )

    @api.depends("program_id.code", "period_start", "period_end")
    def _compute_display_name(self):
        for report in self:
            parts = ["CNIME", report.program_id.code or ""]
            if report.period_start:
                start = report.period_start.strftime("%Y-%m")
                end = report.period_end and report.period_end.strftime("%Y-%m")
                parts.append(f"{start} / {end}" if end and end != start else start)
            report.display_name = " ".join(part for part in parts if part)

    def _generate_report_data(self):
        """Compile the report snapshot. Called explicitly by action_generate,
        never as a compute, so a submitted report is never silently rewritten."""
        for report in self:
            if not (report.program_id and report.period_start and report.period_end):
                raise UserError(_("Set the program and the period before generating."))
            program = report.program_id

            # Import data - admissions in period
            admissions = self.env["l10n_py.maquila.admission"].search(
                [
                    ("program_id", "=", program.id),
                    ("date_admission", ">=", report.period_start),
                    ("date_admission", "<=", report.period_end),
                ]
            )
            import_lines = []
            for adm in admissions:
                for line in adm.line_ids:
                    import_lines.append(
                        {
                            "dispatch": adm.name,
                            "product": line.product_id.name,
                            "quantity": line.quantity,
                            "fob_value": line.fob_value,
                        }
                    )
            report.import_data = (
                json.dumps(import_lines, indent=2) if import_lines else False
            )

            # Export data - exports in period
            exports = self.env["l10n_py.maquila.export"].search(
                [
                    ("program_id", "=", program.id),
                    ("date_export", ">=", report.period_start),
                    ("date_export", "<=", report.period_end),
                ]
            )
            export_lines = []
            for exp in exports:
                for line in exp.line_ids:
                    export_lines.append(
                        {
                            "dispatch": exp.name,
                            "product": line.product_id.name,
                            "quantity": line.quantity,
                            "fob_value": line.fob_value,
                        }
                    )
            report.export_data = (
                json.dumps(export_lines, indent=2) if export_lines else False
            )

            # Production data
            productions = self.env["mrp.production"].search(
                [
                    ("l10n_py_maquila_program_id", "=", program.id),
                    ("date_start", ">=", report.period_start),
                    ("date_start", "<=", report.period_end),
                    ("state", "=", "done"),
                ]
            )
            prod_lines = []
            for prod in productions:
                prod_lines.append(
                    {
                        "reference": prod.name,
                        "product": prod.product_id.name,
                        "quantity": prod.qty_produced,
                    }
                )
            report.production_data = (
                json.dumps(prod_lines, indent=2) if prod_lines else False
            )

            # Waste data
            wastes = self.env["l10n_py.maquila.waste"].search(
                [
                    ("program_id", "=", program.id),
                    ("date", ">=", report.period_start),
                    ("date", "<=", report.period_end),
                ]
            )
            waste_lines = []
            for w in wastes:
                waste_lines.append(
                    {
                        "product": w.product_id.name,
                        "quantity": w.quantity,
                        "type": w.waste_type,
                        "destination": w.destination,
                    }
                )
            report.waste_data = (
                json.dumps(waste_lines, indent=2) if waste_lines else False
            )
            consumption = report._consumption_lines(productions, wastes)
            report.consumption_data = (
                json.dumps(consumption, indent=2) if consumption else False
            )

            # Stock balance at period_end (historical), from done stock moves
            # in/out of the maquila location tree up to the cut-off date.
            maquila_loc = self.env.ref(
                "l10n_py_maquila_ops.stock_location_maquila",
                raise_if_not_found=False,
            )
            balance_lines = []
            if maquila_loc:
                dt_to = fields.Datetime.to_datetime(report.period_end) + relativedelta(
                    days=1
                )
                move_line = self.env["stock.move.line"]
                base = [
                    ("state", "=", "done"),
                    ("date", "<", dt_to),
                    ("company_id", "=", program.company_id.id),
                ]
                incoming = move_line._read_group(
                    base + [("location_dest_id", "child_of", maquila_loc.id)],
                    ["product_id"],
                    ["quantity:sum"],
                )
                outgoing = move_line._read_group(
                    base + [("location_id", "child_of", maquila_loc.id)],
                    ["product_id"],
                    ["quantity:sum"],
                )
                balance = {}
                for product, qty in incoming:
                    balance[product] = balance.get(product, 0.0) + qty
                for product, qty in outgoing:
                    balance[product] = balance.get(product, 0.0) - qty
                for product, qty in balance.items():
                    if qty:
                        balance_lines.append({"product": product.name, "quantity": qty})
            report.stock_balance = (
                json.dumps(balance_lines, indent=2) if balance_lines else False
            )

            # VAN total via the shared program method (same figure as the wizard)
            try:
                report.van_total = program._maquila_van_for_period(
                    report.period_start, report.period_end
                )["van_amount"]
            except UserError:
                # No analytic account or no completed production in the period.
                report.van_total = 0.0

    def _consumption_lines(self, productions, wastes):
        """Raw material consumed by the given done manufacturing orders,
        grouped by product, in the product unit of measure, with the
        quantity expected by the bill of materials for what was produced and
        the waste recorded for the product (Decreto 5714/2026 Art. 15 b-d)."""
        totals = {}
        for prod in productions:
            bom = prod.bom_id
            factor = (
                prod.product_uom_id._compute_quantity(
                    prod.qty_produced, bom.product_uom_id
                )
                / bom.product_qty
                if bom and bom.product_qty
                else 0.0
            )
            for move in prod.move_raw_ids.filtered(lambda m: m.state == "done"):
                product = move.product_id
                item = totals.setdefault(
                    product,
                    {
                        "product": product.display_name,
                        "uom": product.uom_id.name,
                        "origin": False,
                        "consumed": 0.0,
                        "bom_quantity": 0.0,
                    },
                )
                item["consumed"] += move.product_uom._compute_quantity(
                    move.quantity, product.uom_id
                )
                bom_line = move.bom_line_id
                if bom_line:
                    item["origin"] = bom_line.l10n_py_origin_type
                    item["bom_quantity"] += bom_line.product_uom_id._compute_quantity(
                        bom_line.product_qty * factor, product.uom_id
                    )
        for product, item in totals.items():
            waste = sum(
                wastes.filtered(lambda w, p=product: w.product_id == p).mapped(
                    "quantity"
                )
            )
            item["waste_quantity"] = waste
            item["waste_pct"] = (
                round(waste / item["consumed"] * 100, 2) if item["consumed"] else 0.0
            )
        return list(totals.values())

    def action_generate(self):
        """Compile the snapshot and move to the generated state."""
        for report in self:
            if report.state == "submitted":
                raise UserError(_("A submitted report cannot be regenerated."))
        self._generate_report_data()
        self.write({"state": "generated"})

    def action_validate(self):
        self.write({"state": "validated"})

    def action_submit(self):
        if any(not report.submission_protocol for report in self):
            raise UserError(_("Set the submission protocol before submitting."))
        self.write(
            {
                "state": "submitted",
                "submission_date": fields.Datetime.now(),
            }
        )

    def action_draft(self):
        for report in self:
            if report.state == "submitted":
                raise UserError(_("A submitted report cannot be reset to draft."))
        self.write({"state": "draft"})

    def action_generate_simex_payload(self):
        """Generate the SIMEX payloads (stub for future integration).

        Builds two separate payload groups (cuenta corriente and
        inversion/empleo, per Art. 12) and stores each as a JSON
        attachment on the report. Regenerating in ``validated`` replaces
        the previous SIMEX attachments; once ``submitted``, the payload
        that was actually sent is frozen and generation is blocked.
        """
        self.ensure_one()
        if self.state == "submitted":
            raise UserError(
                _(
                    "A submitted report's SIMEX payload is frozen and cannot "
                    "be regenerated. What was sent stays as is."
                )
            )
        self.check_access("write")
        # SIMEX integration stub - offline payload generation
        payload_cuenta_corriente = {
            "programa": self.program_id.code,
            "periodo_inicio": str(self.period_start),
            "periodo_fin": str(self.period_end),
            "importaciones": json.loads(self.import_data or "[]"),
            "exportaciones": json.loads(self.export_data or "[]"),
            "produccion": json.loads(self.production_data or "[]"),
            "consumo": json.loads(self.consumption_data or "[]"),
            "residuos": json.loads(self.waste_data or "[]"),
            "stock_balance": json.loads(self.stock_balance or "[]"),
        }
        payload_inversion_empleo = {
            "programa": self.program_id.code,
            "periodo_inicio": str(self.period_start),
            "periodo_fin": str(self.period_end),
            "van_total": self.van_total,
            "empleo": self.employment_count,
        }

        existing_attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
                ("name", "=like", "simex_%"),
            ]
        )
        existing_attachments.unlink()

        attachments = self.env["ir.attachment"].create(
            [
                {
                    "name": f"simex_cuenta_corriente_{self.period_end}.json",
                    "res_model": self._name,
                    "res_id": self.id,
                    "mimetype": "application/json",
                    "datas": base64.b64encode(
                        json.dumps(
                            payload_cuenta_corriente, indent=2, default=str
                        ).encode()
                    ),
                },
                {
                    "name": f"simex_inversion_empleo_{self.period_end}.json",
                    "res_model": self._name,
                    "res_id": self.id,
                    "mimetype": "application/json",
                    "datas": base64.b64encode(
                        json.dumps(
                            payload_inversion_empleo, indent=2, default=str
                        ).encode()
                    ),
                },
            ]
        )

        self.message_post(
            body=_("SIMEX payload generated (offline mode): %s attachments")
            % len(attachments),
            attachment_ids=attachments.ids,
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("SIMEX Payload Generated"),
                "message": _("SIMEX payload generated successfully (offline mode)."),
                "sticky": False,
                "type": "success",
            },
        }
