# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models


class MaquilaProgram(models.Model):
    _inherit = "l10n_py.maquila.program"

    admission_ids = fields.One2many(
        "l10n_py.maquila.admission",
        "program_id",
        string="Admissions",
    )
    admission_count = fields.Integer(compute="_compute_admission_count")
    export_ids = fields.One2many(
        "l10n_py.maquila.export",
        "program_id",
        string="Exports",
    )
    export_count = fields.Integer(compute="_compute_export_count")
    guarantee_ids = fields.One2many(
        "l10n_py.maquila.guarantee",
        "program_id",
        string="Guarantees",
    )
    guarantee_count = fields.Integer(compute="_compute_guarantee_count")
    tum_declaration_ids = fields.One2many(
        "l10n_py.maquila.tum.declaration",
        "program_id",
        string="TUM Declarations",
    )
    tum_declaration_count = fields.Integer(compute="_compute_tum_declaration_count")
    tum_salary_account_ids = fields.Many2many(
        "account.account",
        "l10n_py_maquila_program_salary_account_rel",
        "program_id",
        "account_id",
        string="Salary Accounts",
        help="Journal items on these accounts linked to the program (by the "
        "program field of the entry or by its analytic account) are component "
        "c) of the value added: salaries and remunerations paid in the "
        "country, including social security contributions "
        "(Ley 7547/2025 Art. 37 c).",
    )
    tum_depreciation_account_ids = fields.Many2many(
        "account.account",
        "l10n_py_maquila_program_depreciation_account_rel",
        "program_id",
        "account_id",
        string="Depreciation Accounts",
        help="Journal items on these accounts linked to the program are "
        "component d) of the value added: depreciation of capital goods owned "
        "by the maquiladora (Ley 7547/2025 Art. 37 d).",
    )
    tum_expense_account_id = fields.Many2one(
        "account.account",
        string="TUM Expense Account",
    )
    tum_payable_account_id = fields.Many2one(
        "account.account",
        string="TUM Payable Account",
    )

    @api.depends("admission_ids")
    def _compute_admission_count(self):
        for rec in self:
            rec.admission_count = len(rec.admission_ids)

    @api.depends("export_ids")
    def _compute_export_count(self):
        for rec in self:
            rec.export_count = len(rec.export_ids)

    @api.depends("guarantee_ids")
    def _compute_guarantee_count(self):
        for rec in self:
            rec.guarantee_count = len(rec.guarantee_ids)

    @api.depends("tum_declaration_ids")
    def _compute_tum_declaration_count(self):
        for rec in self:
            rec.tum_declaration_count = len(rec.tum_declaration_ids)

    def action_view_tum_declarations(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("TUM Declarations"),
            "res_model": "l10n_py.maquila.tum.declaration",
            "view_mode": "list,form",
            "domain": [("program_id", "=", self.id)],
            "context": {"default_program_id": self.id},
        }

    def _l10n_py_maquila_tum_share(self, line):
        """Share of a journal item that belongs to the program: the whole item
        when its entry carries the program, otherwise the percentage of the
        program analytic account in its analytic distribution."""
        if line.move_id.l10n_py_maquila_program_id == self:
            return 1.0
        analytic = self.analytic_account_id
        if not analytic or not line.analytic_distribution:
            return 0.0
        share = 0.0
        for key, pct in line.analytic_distribution.items():
            if str(analytic.id) in key.split(","):
                share += pct / 100.0
        return share

    def _l10n_py_maquila_tum_classify(self, line):
        """Return (component, sign, criterion) of a journal item for the value
        added of Ley 7547/2025 Art. 37, or (False, 0, False) if it is not part
        of it."""
        if line.account_id in self.tum_salary_account_ids:
            return "c", 1, _("Salary account")
        if line.account_id in self.tum_depreciation_account_ids:
            return "d", 1, _("Depreciation account")
        if line.display_type != "product":
            return False, 0, False
        move = line.move_id
        is_service = not line.product_id or line.product_id.type == "service"
        if move.move_type in ("in_invoice", "in_refund", "in_receipt"):
            country = move.commercial_partner_id.country_id
            if not country or country != self.company_id.country_id:
                return False, 0, False
            if is_service:
                return "b", 1, _("Vendor bill, domestic supplier, service")
            return "a", 1, _("Vendor bill, domestic supplier, goods")
        if move.move_type in ("out_invoice", "out_refund") and is_service:
            return "e", -1, _("Customer invoice, maquila service")
        return False, 0, False

    def _l10n_py_maquila_tum_values(self, date_from, date_to):
        """Value added in the national territory (Ley 7547/2025 Art. 37) and
        export invoice value of the program for a period, in company currency.

        Only posted journal items of the program company in the period are
        considered, linked to the program by the program field of the entry or
        by the program analytic account. Returns a dict with the value added
        lines (one per component and document), the export invoices and their
        amount."""
        self.ensure_one()
        company = self.company_id
        link = [("move_id.l10n_py_maquila_program_id", "=", self.id)]
        if self.analytic_account_id:
            link = [
                "|",
                ("analytic_distribution", "in", [self.analytic_account_id.id]),
            ] + link
        aml = self.env["account.move.line"].search(
            [
                ("company_id", "=", company.id),
                ("parent_state", "=", "posted"),
                ("date", ">=", date_from),
                ("date", "<=", date_to),
            ]
            + link
        )
        grouped = defaultdict(lambda: self.env["account.move.line"])
        amounts = defaultdict(float)
        criteria = {}
        for line in aml:
            component, sign, criterion = self._l10n_py_maquila_tum_classify(line)
            if not component:
                continue
            share = self._l10n_py_maquila_tum_share(line)
            if not share:
                continue
            key = (component, line.move_id)
            grouped[key] |= line
            amounts[key] += sign * line.balance * share
            criteria[key] = criterion
        lines = []
        for (component, move), items in grouped.items():
            key = (component, move)
            lines.append(
                {
                    "component": component,
                    "name": move.name or move.ref or "/",
                    "move_id": move.id,
                    "partner_id": move.commercial_partner_id.id,
                    "move_line_ids": [(6, 0, items.ids)],
                    "criterion": criteria[key],
                    "amount": company.currency_id.round(amounts[key]),
                }
            )
        invoices = self.env["account.move"].search(
            [
                ("company_id", "=", company.id),
                ("l10n_py_maquila_program_id", "=", self.id),
                ("move_type", "in", ("out_invoice", "out_refund")),
                ("state", "=", "posted"),
                ("invoice_date", ">=", date_from),
                ("invoice_date", "<=", date_to),
            ]
        )
        return {
            "lines": lines,
            "value_added_amount": sum(line["amount"] for line in lines),
            "export_invoices": invoices,
            "export_invoice_amount": sum(invoices.mapped("amount_total_signed")),
        }

    def action_view_admissions(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Admissions",
            "res_model": "l10n_py.maquila.admission",
            "view_mode": "list,form",
            "domain": [("program_id", "=", self.id)],
            "context": {"default_program_id": self.id},
        }

    def action_view_exports(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Exports",
            "res_model": "l10n_py.maquila.export",
            "view_mode": "list,form",
            "domain": [("program_id", "=", self.id)],
            "context": {"default_program_id": self.id},
        }

    def action_view_guarantees(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Guarantees",
            "res_model": "l10n_py.maquila.guarantee",
            "view_mode": "list,form",
            "domain": [("program_id", "=", self.id)],
            "context": {"default_program_id": self.id},
        }
