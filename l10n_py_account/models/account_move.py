# l10n_py_account/models/account_move.py

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # ============== CAMPOS CONTABILIDAD PARAGUAY ==============

    authorization_id = fields.Many2one(
        "account.authorization",
        string="Timbrado",
        domain="[('company_id', '=', company_id), ('active', '=', True), ('state', '!=', 'expired')]",
        help="Timbrado utilizado para esta factura",
    )

    invoice_number = fields.Integer(
        string="Número de Factura", help="Número de factura según timbrado autorizado"
    )

    # ============== CONSTRAINT METHODS ==============

    @api.constrains("authorization_id", "invoice_number")
    def _check_authorization_number(self):
        """Validar que el número de factura esté dentro del rango autorizado"""
        for move in self:
            if move.authorization_id and move.invoice_number:
                move.authorization_id.check_number_available(move.invoice_number)

    @api.constrains("authorization_id")
    def _check_authorization_validity(self):
        """Validar que el timbrado esté vigente"""
        for move in self:
            if move.authorization_id:
                move.authorization_id.check_validity()

    # ============== ONCHANGE METHODS ==============

    @api.onchange("authorization_id")
    def _onchange_authorization_id(self):
        """Actualizar número de factura cuando cambia el timbrado"""
        if self.authorization_id and not self.invoice_number:
            self.invoice_number = self.authorization_id.next_number
