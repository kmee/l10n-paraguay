# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class MaquilaTaxCreditWizard(models.TransientModel):
    _name = "l10n_py.maquila.tax.credit.wizard"
    _description = "Maquila Tax Credit (IVA) Wizard"

    program_id = fields.Many2one(
        "l10n_py.maquila.program",
        required=True,
        domain="[('state', '=', 'active')]",
    )
    action_type = fields.Selection(
        [
            ("compensate", "Compensate"),
            ("transfer", "Transfer to Third Party"),
        ],
        required=True,
        default="compensate",
    )
    transfer_partner_id = fields.Many2one(
        "res.partner",
        string="Transfer To",
    )
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.ref("base.USD"),
    )
    amount = fields.Monetary(required=True)

    def action_execute(self):
        self.ensure_one()
        if self.action_type == "transfer" and not self.transfer_partner_id:
            raise UserError(_("Please select a partner for the transfer."))
        if not self.amount:
            raise UserError(_("Amount must be greater than zero."))

        ref = _("IVA Credit %(action_type)s - %(program)s - %(date)s") % {
            "action_type": self.action_type,
            "program": self.program_id.code,
            "date": fields.Date.today(),
        }
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.env.company.id)],
            limit=1,
        )
        if not journal:
            raise UserError(_("No miscellaneous journal found."))
        account = journal.default_account_id
        if not account:
            raise UserError(
                _("Journal '%(journal)s' has no default account configured.")
                % {"journal": journal.name}
            )
        move_vals = {
            "move_type": "entry",
            "date": fields.Date.today(),
            "ref": ref,
            "l10n_py_maquila_program_id": self.program_id.id,
            "journal_id": journal.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": ref,
                        "debit": self.amount,
                        "credit": 0,
                        "account_id": account.id,
                        "partner_id": self.transfer_partner_id.id
                        if self.action_type == "transfer"
                        else False,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": ref,
                        "debit": 0,
                        "credit": self.amount,
                        "account_id": account.id,
                    },
                ),
            ],
        }
        move = self.env["account.move"].create(move_vals)
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
        }
