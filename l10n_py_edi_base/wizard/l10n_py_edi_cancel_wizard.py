# l10n_py_edi_base/wizard/l10n_py_edi_cancel_wizard.py

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class EDICancelWizard(models.TransientModel):
    _name = "l10n_py.edi.cancel.wizard"
    _description = "Wizard para cancelar documento EDI"

    invoice_id = fields.Many2one("account.move", string="Factura", required=True)
    motive = fields.Text(string="Motivo de Cancelación", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_id"):
            res["invoice_id"] = self.env.context["active_id"]
        return res

    def action_cancel(self):
        """Cancelar documento EDI"""
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No se seleccionó una factura"))

        if not self.invoice_id.l10n_py_cdc:
            raise UserError(_("La factura no tiene CDC, no se puede cancelar"))

        self.invoice_id.action_cancel_edi()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Cancelación Exitosa"),
                "message": _("El documento ha sido cancelado"),
                "type": "success",
                "sticky": False,
            },
        }
