# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

MRP_FIELDS = (
    "total_cost",
    "national_cost",
    "mercosul_cost",
    "imported_cost",
)


class MaquilaTumWizard(models.TransientModel):
    _inherit = "l10n_py.maquila.tum.wizard"

    total_cost = fields.Monetary(readonly=True)
    national_cost = fields.Monetary(
        string="National Cost (PY)",
        readonly=True,
    )
    mercosul_cost = fields.Monetary(readonly=True)
    imported_cost = fields.Monetary(readonly=True)
    mrp_van_amount = fields.Monetary(
        string="MRP National Content",
        readonly=True,
        help="Program analytic cost minus Mercosul and imported inputs "
        "consumed by the completed manufacturing orders. Informative: the "
        "TUM base uses the value added of Ley 7547/2025 Art. 37.",
    )
    van_warning = fields.Char(readonly=True)

    def action_compute(self):
        """Keep the Art. 37 value added computed by l10n_py_maquila_ops as the
        TUM base and add, for information, the origin split of the inputs
        consumed by the completed manufacturing orders of the period."""
        self.ensure_one()
        result = super().action_compute()
        program = self.program_id
        for field_name in MRP_FIELDS + ("mrp_van_amount",):
            self[field_name] = 0.0
        has_completed_production = bool(
            self.env["mrp.production"].search_count(
                [
                    ("l10n_py_maquila_program_id", "=", program.id),
                    ("date_start", ">=", self.period_start),
                    ("date_start", "<=", self.period_end),
                    ("state", "=", "done"),
                ]
            )
        )
        if not program.analytic_account_id or not has_completed_production:
            self.van_warning = _(
                "The MRP origin split of the inputs needs an analytic account "
                "on program %(program)s and a completed manufacturing order in "
                "the period. It is informative only and does not change the "
                "TUM base.",
                program=program.code,
            )
            return result
        self.van_warning = False
        vals = program._maquila_van_for_period(self.period_start, self.period_end)
        company = program.company_id
        for field_name in MRP_FIELDS:
            self[field_name] = company.currency_id._convert(
                vals[field_name], self.currency_id, company, self.period_end
            )
        self.mrp_van_amount = company.currency_id._convert(
            vals["van_amount"], self.currency_id, company, self.period_end
        )
        return result
