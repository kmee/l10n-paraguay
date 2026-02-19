# l10n_py_account/models/account_move.py

from num2words import num2words

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # ============== CAMPOS CONTABILIDAD PARAGUAY ==============

    l10n_py_authorization_id = fields.Many2one(
        "account.authorization",
        string="Timbrado",
        domain=(
            "[('company_id', '=', company_id), "
            "('active', '=', True), "
            "('state', '!=', 'expired')]"
        ),
        help="Timbrado utilizado para esta factura",
    )

    l10n_py_invoice_number = fields.Integer(
        string="Número de Factura",
        help="Número de factura según timbrado autorizado",
    )

    l10n_py_full_invoice_number = fields.Char(
        string="Número Completo",
        compute="_compute_l10n_py_full_invoice_number",
        store=True,
        help="Número completo de factura (formato: 001-001-0000001)",
    )

    # ============== CAMPOS IVA BREAKDOWN ==============

    l10n_py_amount_subtotal_10 = fields.Monetary(
        string="Subtotal IVA 10%",
        compute="_compute_l10n_py_iva",
        store=True,
        currency_field="currency_id",
    )

    l10n_py_amount_iva_10 = fields.Monetary(
        string="IVA 10%",
        compute="_compute_l10n_py_iva",
        store=True,
        currency_field="currency_id",
    )

    l10n_py_amount_subtotal_5 = fields.Monetary(
        string="Subtotal IVA 5%",
        compute="_compute_l10n_py_iva",
        store=True,
        currency_field="currency_id",
    )

    l10n_py_amount_iva_5 = fields.Monetary(
        string="IVA 5%",
        compute="_compute_l10n_py_iva",
        store=True,
        currency_field="currency_id",
    )

    l10n_py_amount_exempt = fields.Monetary(
        string="Monto Exento",
        compute="_compute_l10n_py_iva",
        store=True,
        currency_field="currency_id",
    )

    l10n_py_amount_iva_total = fields.Monetary(
        string="Total IVA",
        compute="_compute_l10n_py_iva",
        store=True,
        currency_field="currency_id",
    )

    l10n_py_amount_total_words = fields.Char(
        string="Total en Letras",
        compute="_compute_l10n_py_amount_total_words",
    )

    # ============== COMPUTE METHODS ==============

    @api.depends(
        "l10n_py_authorization_id",
        "l10n_py_invoice_number",
    )
    def _compute_l10n_py_full_invoice_number(self):
        """Calcular número completo de factura (formato: 001-001-0000001)"""
        for move in self:
            if move.l10n_py_authorization_id and move.l10n_py_invoice_number:
                auth = move.l10n_py_authorization_id
                number_str = str(move.l10n_py_invoice_number).zfill(7)
                move.l10n_py_full_invoice_number = (
                    f"{auth.establishment}-" f"{auth.expedition_point}-" f"{number_str}"
                )
            else:
                move.l10n_py_full_invoice_number = False

    @api.depends("invoice_line_ids.price_subtotal", "invoice_line_ids.tax_ids")
    def _compute_l10n_py_iva(self):
        """Calcular desglose de IVA por tasa (10%, 5%, exento)"""
        for move in self:
            subtotal_10 = 0.0
            iva_10 = 0.0
            subtotal_5 = 0.0
            iva_5 = 0.0
            exempt = 0.0

            for line in move.invoice_line_ids.filtered(
                lambda l: l.display_type == "product"
            ):
                tax_rate = 0
                for tax in line.tax_ids:
                    if tax.amount == 10:
                        tax_rate = 10
                    elif tax.amount == 5:
                        tax_rate = 5

                if tax_rate == 10:
                    subtotal_10 += line.price_subtotal
                    iva_10 += line.price_subtotal * 10 / 100
                elif tax_rate == 5:
                    subtotal_5 += line.price_subtotal
                    iva_5 += line.price_subtotal * 5 / 100
                else:
                    exempt += line.price_subtotal

            move.l10n_py_amount_subtotal_10 = subtotal_10
            move.l10n_py_amount_iva_10 = iva_10
            move.l10n_py_amount_subtotal_5 = subtotal_5
            move.l10n_py_amount_iva_5 = iva_5
            move.l10n_py_amount_exempt = exempt
            move.l10n_py_amount_iva_total = iva_10 + iva_5

    @api.depends("amount_total", "currency_id")
    def _compute_l10n_py_amount_total_words(self):
        """Convertir total a letras en español"""
        for move in self:
            if move.amount_total:
                currency_name = move.currency_id.currency_unit_label or "guaraníes"
                amount_words = num2words(int(move.amount_total), lang="es")
                move.l10n_py_amount_total_words = (
                    f"{amount_words} {currency_name}".capitalize()
                )
            else:
                move.l10n_py_amount_total_words = False

    # ============== CONSTRAINT METHODS ==============

    @api.constrains("l10n_py_authorization_id", "l10n_py_invoice_number")
    def _check_authorization_number(self):
        """Validar que el número de factura esté dentro del rango autorizado"""
        for move in self:
            if move.l10n_py_authorization_id and move.l10n_py_invoice_number:
                move.l10n_py_authorization_id.check_number_available(
                    move.l10n_py_invoice_number,
                    exclude_move_id=move.id,
                )

    @api.constrains("l10n_py_authorization_id")
    def _check_authorization_validity(self):
        """Validar que el timbrado esté vigente"""
        for move in self:
            if move.l10n_py_authorization_id:
                move.l10n_py_authorization_id.check_validity()

    # ============== ONCHANGE METHODS ==============

    @api.onchange("l10n_py_authorization_id")
    def _onchange_authorization_id(self):
        """Actualizar número de factura cuando cambia el timbrado"""
        if self.l10n_py_authorization_id and not self.l10n_py_invoice_number:
            self.l10n_py_invoice_number = self.l10n_py_authorization_id.next_number
