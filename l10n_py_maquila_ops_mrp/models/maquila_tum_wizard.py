# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models

VAN_FIELDS = (
    "total_cost",
    "national_cost",
    "mercosul_cost",
    "imported_cost",
    "van_amount",
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
    van_warning = fields.Char(readonly=True)

    def action_compute(self):
        """Extend the base computation to derive van_amount from
        l10n_py_maquila_mrp's shared VAN calculation, so the TUM wizard and
        the VAN wizard always report the same figure for the same period.
        """
        self.ensure_one()
        result = super().action_compute()
        program = self.program_id
        if not program.analytic_account_id:
            # Let the shared method raise its own configuration error, with
            # the same message used by the VAN wizard.
            program._maquila_van_for_period(self.period_start, self.period_end)
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
        if not has_completed_production:
            # No completed production in the period: the origin split of the
            # cost cannot be determined, so the VAN is left at zero and the
            # TUM base falls back to the export invoice amount, matching the
            # behavior of l10n_py_maquila_ops without this bridge installed.
            for field_name in VAN_FIELDS:
                self[field_name] = 0.0
            self.van_warning = _(
                "No completed production was found for program %(program)s in "
                "the selected period, so the VAN could not be determined. The "
                "TUM base uses the export invoice amount only.",
                program=program.code,
            )
            return result
        self.van_warning = False
        vals = program._maquila_van_for_period(self.period_start, self.period_end)
        company = self.env.company
        for field_name in VAN_FIELDS:
            self[field_name] = company.currency_id._convert(
                vals[field_name], self.currency_id, company, self.period_end
            )
        return result
