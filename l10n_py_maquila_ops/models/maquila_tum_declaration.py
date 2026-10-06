# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# Ley 7547/2025 Art. 37: components of the value added in the national
# territory.
VALUE_ADDED_COMPONENTS = [
    ("a", "a) Goods acquired in the country"),
    ("b", "b) Services contracted in the country"),
    ("c", "c) Salaries and remunerations, incl. social security"),
    ("d", "d) Depreciation of the maquiladora's capital goods"),
    ("e", "e) Remuneration received for the maquila service"),
]


class MaquilaTumDeclaration(models.Model):
    """Monthly summary of the Tributo Unico Maquila.

    Ley 7547/2025 Art. 37: 1% over the greater of the value added in the
    national territory (components a to e) and the export invoice value.
    Decreto 5714/2026 Art. 43: monthly sworn declaration, mandatory even
    without exports. The official DNIT form is not modelled here: this record
    is the supporting summary for it.
    """

    _name = "l10n_py.maquila.tum.declaration"
    _description = "Maquila Single Tax (TUM) Monthly Declaration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from desc, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    program_id = fields.Many2one(
        "l10n_py.maquila.program",
        required=True,
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="program_id.company_id",
        store=True,
        index=True,
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    date_from = fields.Date(
        string="Period Start",
        required=True,
        default=lambda self: fields.Date.context_today(self).replace(day=1)
        - relativedelta(months=1),
    )
    date_to = fields.Date(
        string="Period End",
        compute="_compute_date_to",
        store=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        "l10n_py.maquila.tum.declaration.line",
        "declaration_id",
        string="Value Added Lines",
    )
    export_invoice_ids = fields.Many2many(
        "account.move",
        "l10n_py_maquila_tum_declaration_invoice_rel",
        "declaration_id",
        "move_id",
        string="Export Invoices",
        readonly=True,
    )
    export_invoice_amount = fields.Monetary(
        string="Export Invoice Value",
        readonly=True,
        help="Posted customer invoices and refunds of the program in the "
        "period, in company currency (Ley 7547/2025 Art. 37).",
    )
    amount_a = fields.Monetary(
        string="a) Goods Acquired in the Country",
        compute="_compute_amounts",
        store=True,
    )
    amount_b = fields.Monetary(
        string="b) Services Contracted in the Country",
        compute="_compute_amounts",
        store=True,
    )
    amount_c = fields.Monetary(
        string="c) Salaries and Social Security",
        compute="_compute_amounts",
        store=True,
    )
    amount_d = fields.Monetary(
        string="d) Depreciation of Capital Goods",
        compute="_compute_amounts",
        store=True,
    )
    amount_e = fields.Monetary(
        string="e) Maquila Service Remuneration",
        compute="_compute_amounts",
        store=True,
    )
    amount_manual = fields.Monetary(
        string="Of Which Entered Manually",
        compute="_compute_amounts",
        store=True,
    )
    value_added_amount = fields.Monetary(
        string="Value Added (Art. 37)",
        compute="_compute_amounts",
        store=True,
    )
    tax_base = fields.Monetary(compute="_compute_amounts", store=True)
    tax_base_origin = fields.Selection(
        [
            ("value_added", "Value added"),
            ("export_invoice", "Export invoice value"),
        ],
        compute="_compute_amounts",
        store=True,
    )
    tax_rate = fields.Float(
        string="Rate %",
        default=1.0,
        readonly=True,
        help="Ley 7547/2025 Art. 37: 1%.",
    )
    tax_amount = fields.Monetary(
        string="Tributo Unico",
        compute="_compute_amounts",
        store=True,
    )
    computed_on = fields.Datetime(readonly=True)
    dnit_reference = fields.Char(
        string="DNIT Filing Reference",
        tracking=True,
        help="Number of the sworn declaration filed with the DNIT.",
    )
    expense_account_id = fields.Many2one(
        "account.account",
        compute="_compute_accounts",
        store=True,
        readonly=False,
    )
    payable_account_id = fields.Many2one(
        "account.account",
        compute="_compute_accounts",
        store=True,
        readonly=False,
    )
    move_id = fields.Many2one(
        "account.move",
        string="Journal Entry",
        readonly=True,
        copy=False,
    )
    warning_message = fields.Text(compute="_compute_warning_message")

    _sql_constraints = [
        (
            "program_period_uniq",
            "unique(program_id, date_from)",
            "There is already a declaration for this program and period.",
        )
    ]

    @api.depends("date_from")
    def _compute_date_to(self):
        for rec in self:
            rec.date_to = rec.date_from and (rec.date_from + relativedelta(day=31))

    @api.depends("program_id.code", "date_from")
    def _compute_name(self):
        for rec in self:
            period = rec.date_from and rec.date_from.strftime("%Y-%m") or ""
            rec.name = _(
                "TUM %(program)s %(period)s",
                program=rec.program_id.code or "",
                period=period,
            )

    @api.depends("program_id")
    def _compute_accounts(self):
        for rec in self:
            rec.expense_account_id = rec.program_id.tum_expense_account_id
            rec.payable_account_id = rec.program_id.tum_payable_account_id

    @api.depends(
        "line_ids.amount",
        "line_ids.component",
        "line_ids.source",
        "export_invoice_amount",
        "tax_rate",
    )
    def _compute_amounts(self):
        for rec in self:
            totals = defaultdict(float)
            manual = 0.0
            for line in rec.line_ids:
                totals[line.component] += line.amount
                if line.source == "manual":
                    manual += line.amount
            for code, _label in VALUE_ADDED_COMPONENTS:
                rec[f"amount_{code}"] = totals[code]
            rec.amount_manual = manual
            rec.value_added_amount = sum(totals.values())
            if rec.value_added_amount >= rec.export_invoice_amount:
                rec.tax_base = rec.value_added_amount
                rec.tax_base_origin = "value_added"
            else:
                rec.tax_base = rec.export_invoice_amount
                rec.tax_base_origin = "export_invoice"
            rec.tax_amount = rec.currency_id.round(
                max(rec.tax_base, 0.0) * rec.tax_rate / 100
            )

    @api.depends("program_id", "line_ids")
    def _compute_warning_message(self):
        for rec in self:
            program = rec.program_id
            msgs = []
            if program and not program.tum_salary_account_ids:
                msgs.append(
                    _(
                        "No salary accounts are configured on the program: "
                        "component c) only has manual lines."
                    )
                )
            if program and not program.tum_depreciation_account_ids:
                msgs.append(
                    _(
                        "No depreciation accounts are configured on the "
                        "program: component d) only has manual lines."
                    )
                )
            rec.warning_message = "\n".join(msgs) or False

    @api.constrains("date_from")
    def _check_date_from(self):
        for rec in self:
            if rec.date_from and rec.date_from.day != 1:
                raise ValidationError(
                    _(
                        "The declaration is monthly (Decreto 5714/2026 Art. 43): "
                        "the period must start on the first day of a month."
                    )
                )

    def _check_draft(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("Declaration %(name)s is confirmed.", name=rec.name))

    def action_compute(self):
        """Rebuild the automatic lines from the accounting; manual lines are
        kept."""
        self._check_draft()
        line_model = self.env["l10n_py.maquila.tum.declaration.line"]
        for rec in self:
            rec.line_ids.filtered(lambda line: line.source == "auto").unlink()
            values = rec.program_id._l10n_py_maquila_tum_values(
                rec.date_from, rec.date_to
            )
            line_model.create(
                [
                    dict(vals, declaration_id=rec.id, source="auto")
                    for vals in values["lines"]
                ]
            )
            rec.write(
                {
                    "export_invoice_ids": [(6, 0, values["export_invoices"].ids)],
                    "export_invoice_amount": values["export_invoice_amount"],
                    "computed_on": fields.Datetime.now(),
                }
            )
        return True

    def action_confirm(self):
        self._check_draft()
        for rec in self:
            if not rec.computed_on:
                raise UserError(
                    _("Compute the declaration %(name)s first.", name=rec.name)
                )
        # A declaration with zero amounts is still due (Decreto 5714 Art. 43).
        self.write({"state": "confirmed"})
        return True

    def action_draft(self):
        for rec in self:
            if rec.move_id.state == "posted":
                raise UserError(
                    _(
                        "Reset the journal entry %(move)s to draft before "
                        "reopening the declaration.",
                        move=rec.move_id.display_name,
                    )
                )
        self.move_id.filtered(lambda m: m.state == "draft").unlink()
        self.write({"state": "draft"})
        return True

    def action_generate_move(self):
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Confirm the declaration first."))
        if self.move_id:
            raise UserError(_("The journal entry was already generated."))
        if self.currency_id.is_zero(self.tax_amount):
            raise UserError(_("The Tributo Unico amount is zero."))
        if not self.expense_account_id or not self.payable_account_id:
            raise UserError(_("Set the expense and payable accounts."))
        journal = self.env["account.journal"].search(
            [
                ("type", "=", "general"),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if not journal:
            raise UserError(_("No miscellaneous journal found."))
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": self.date_to,
                "ref": self.name,
                "journal_id": journal.id,
                "company_id": self.company_id.id,
                "l10n_py_maquila_program_id": self.program_id.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.name,
                            "account_id": self.expense_account_id.id,
                            "debit": self.tax_amount,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": self.name,
                            "account_id": self.payable_account_id.id,
                            "debit": 0.0,
                            "credit": self.tax_amount,
                        },
                    ),
                ],
            }
        )
        self.move_id = move
        return self.action_view_move()

    def action_view_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
        }

    def unlink(self):
        self._check_draft()
        return super().unlink()


class MaquilaTumDeclarationLine(models.Model):
    _name = "l10n_py.maquila.tum.declaration.line"
    _description = "Maquila Single Tax (TUM) Declaration Value Added Line"
    _order = "component, source, id"

    declaration_id = fields.Many2one(
        "l10n_py.maquila.tum.declaration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(related="declaration_id.company_id", store=True)
    currency_id = fields.Many2one(related="declaration_id.currency_id")
    component = fields.Selection(VALUE_ADDED_COMPONENTS, required=True)
    source = fields.Selection(
        [("auto", "Accounting"), ("manual", "Manual")],
        required=True,
        default="manual",
    )
    name = fields.Char(string="Description", required=True)
    move_id = fields.Many2one("account.move", string="Document", readonly=True)
    partner_id = fields.Many2one("res.partner", readonly=True)
    move_line_ids = fields.Many2many(
        "account.move.line",
        string="Journal Items",
        readonly=True,
    )
    criterion = fields.Char(
        readonly=True,
        help="Why the journal items were classified in this component.",
    )
    amount = fields.Monetary(required=True)
    note = fields.Char(
        string="Support",
        help="For manual lines: the document that supports the amount "
        "(payroll, social security payment, depreciation schedule).",
    )

    @api.constrains("source", "note")
    def _check_manual_note(self):
        for line in self:
            if line.source == "manual" and not line.note:
                raise ValidationError(
                    _(
                        "Manual line %(name)s needs the supporting document.",
                        name=line.name,
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.declaration_id._check_draft()
        return lines

    def write(self, vals):
        self.declaration_id._check_draft()
        return super().write(vals)

    def unlink(self):
        self.declaration_id._check_draft()
        return super().unlink()
