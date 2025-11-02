# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re


class AccountMove(models.Model):
    """
    Extensión del modelo account.move para Paraguay
    Agrega campos específicos de facturación paraguaya
    """
    _inherit = 'account.move'

    # Campos de autorización (Timbrado)
    authorization_id = fields.Many2one(
        'account.authorization',
        string='Timbrado',
        help='Autorización de facturación de la SET',
        copy=False,
        domain="[('company_id', '=', company_id), ('active', '=', True), ('state', '=', 'valid')]"
    )

    invoice_number = fields.Integer(
        string='Número de Factura',
        help='Número secuencial de la factura',
        copy=False,
        readonly=True,
    )

    full_invoice_number = fields.Char(
        string='Número Completo',
        compute='_compute_full_invoice_number',
        store=True,
        help='Formato: 001-001-0000001'
    )

    # Campos de montos IVA
    amount_iva_5 = fields.Monetary(
        string='IVA 5%',
        compute='_compute_amount_iva',
        store=True,
        currency_field='currency_id',
        help='Monto de IVA al 5%'
    )

    amount_iva_10 = fields.Monetary(
        string='IVA 10%',
        compute='_compute_amount_iva',
        store=True,
        currency_field='currency_id',
        help='Monto de IVA al 10%'
    )

    amount_iva_total = fields.Monetary(
        string='Total IVA',
        compute='_compute_amount_iva',
        store=True,
        currency_field='currency_id',
        help='Total de IVA (5% + 10%)'
    )

    # Campos de subtotales
    amount_subtotal_5 = fields.Monetary(
        string='Subtotal 5%',
        compute='_compute_amount_iva',
        store=True,
        currency_field='currency_id',
        help='Base imponible para IVA 5%'
    )

    amount_subtotal_10 = fields.Monetary(
        string='Subtotal 10%',
        compute='_compute_amount_iva',
        store=True,
        currency_field='currency_id',
        help='Base imponible para IVA 10%'
    )

    amount_subtotal_exempt = fields.Monetary(
        string='Subtotal Exento',
        compute='_compute_amount_iva',
        store=True,
        currency_field='currency_id',
        help='Monto exento de IVA'
    )

    # Monto en letras
    amount_total_words = fields.Char(
        string='Total en Letras',
        compute='_compute_amount_total_words',
        help='Monto total expresado en letras (guaraníes)'
    )

    @api.depends('authorization_id', 'authorization_id.establishment',
                 'authorization_id.expedition_point', 'invoice_number')
    def _compute_full_invoice_number(self):
        """Genera el número completo de factura en formato XXX-XXX-XXXXXXX"""
        for record in self:
            if record.authorization_id and record.invoice_number:
                record.full_invoice_number = f"{record.authorization_id.establishment}-{record.authorization_id.expedition_point}-{str(record.invoice_number).zfill(7)}"
            else:
                record.full_invoice_number = False

    @api.depends('invoice_line_ids', 'invoice_line_ids.tax_ids',
                 'invoice_line_ids.price_subtotal')
    def _compute_amount_iva(self):
        """Calcula los montos de IVA discriminados por alícuota"""
        for record in self:
            amount_iva_5 = 0.0
            amount_iva_10 = 0.0
            amount_subtotal_5 = 0.0
            amount_subtotal_10 = 0.0
            amount_subtotal_exempt = 0.0

            for line in record.invoice_line_ids:
                # Determinar la alícuota de IVA de la línea
                tax_rate = 0.0
                for tax in line.tax_ids:
                    if tax.amount == 5.0:
                        tax_rate = 5.0
                    elif tax.amount == 10.0:
                        tax_rate = 10.0

                # Calcular subtotales y IVA según la alícuota
                if tax_rate == 5.0:
                    amount_subtotal_5 += line.price_subtotal
                    amount_iva_5 += line.price_subtotal * 0.05
                elif tax_rate == 10.0:
                    amount_subtotal_10 += line.price_subtotal
                    amount_iva_10 += line.price_subtotal * 0.10
                else:
                    amount_subtotal_exempt += line.price_subtotal

            record.amount_iva_5 = amount_iva_5
            record.amount_iva_10 = amount_iva_10
            record.amount_iva_total = amount_iva_5 + amount_iva_10
            record.amount_subtotal_5 = amount_subtotal_5
            record.amount_subtotal_10 = amount_subtotal_10
            record.amount_subtotal_exempt = amount_subtotal_exempt

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        """Convierte el monto total a letras en guaraníes"""
        for record in self:
            if record.amount_total:
                record.amount_total_words = self._number_to_words_py(record.amount_total)
            else:
                record.amount_total_words = ''

    def _number_to_words_py(self, amount):
        """
        Convierte un número a palabras en español (guaraníes)
        Implementación básica - puede mejorarse
        """
        # Diccionarios para conversión
        units = ['', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve']
        tens = ['', 'diez', 'veinte', 'treinta', 'cuarenta', 'cincuenta',
                'sesenta', 'setenta', 'ochenta', 'noventa']
        hundreds = ['', 'ciento', 'doscientos', 'trescientos', 'cuatrocientos',
                    'quinientos', 'seiscientos', 'setecientos', 'ochocientos', 'novecientos']

        special = {
            11: 'once', 12: 'doce', 13: 'trece', 14: 'catorce', 15: 'quince',
            16: 'dieciséis', 17: 'diecisiete', 18: 'dieciocho', 19: 'diecinueve',
            21: 'veintiuno', 22: 'veintidós', 23: 'veintitrés', 24: 'veinticuatro',
            25: 'veinticinco', 26: 'veintiséis', 27: 'veintisiete', 28: 'veintiocho',
            29: 'veintinueve'
        }

        # Convertir a entero
        amount_int = int(amount)

        if amount_int == 0:
            return 'cero guaraníes'

        # Implementación simplificada para montos comunes
        if amount_int < 30 and amount_int in special:
            return f"{special[amount_int]} guaraníes"
        elif amount_int < 10:
            return f"{units[amount_int]} guaraníes"
        elif amount_int < 100:
            tens_digit = amount_int // 10
            units_digit = amount_int % 10
            if units_digit == 0:
                return f"{tens[tens_digit]} guaraníes"
            else:
                return f"{tens[tens_digit]} y {units[units_digit]} guaraníes"

        # Para montos mayores, retornar formato numérico por ahora
        return f"{amount_int:,} guaraníes".replace(',', '.')

    @api.constrains('authorization_id', 'move_type')
    def _check_authorization(self):
        """Valida que las facturas de venta tengan timbrado"""
        for record in self:
            if record.move_type in ['out_invoice', 'out_refund'] and record.state == 'posted':
                if not record.authorization_id:
                    raise ValidationError(
                        _('Las facturas de venta deben tener un timbrado asignado.')
                    )

    def action_post(self):
        """Override del método post para asignar número de factura"""
        for record in self:
            # Asignar número solo a facturas de venta sin número previo
            if record.move_type in ['out_invoice', 'out_refund'] and not record.invoice_number:
                if not record.authorization_id:
                    raise ValidationError(
                        _('Debe seleccionar un timbrado antes de confirmar la factura.')
                    )

                # Validar que el timbrado sea válido
                record.authorization_id.check_validity()

                # Asignar el próximo número disponible
                next_number = record.authorization_id.next_number

                # Verificar que el número esté disponible
                record.authorization_id.check_number_available(next_number)

                # Asignar el número
                record.invoice_number = next_number

        return super(AccountMove, self).action_post()

    def _get_name_invoice_report(self):
        """Personaliza el nombre del reporte de factura"""
        self.ensure_one()
        if self.move_type == 'out_invoice':
            return 'l10n_py.report_invoice_document_py'
        return super(AccountMove, self)._get_name_invoice_report()
