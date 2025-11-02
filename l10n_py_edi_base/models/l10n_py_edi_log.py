# -*- coding: utf-8 -*-
# l10n_py_edi_base/models/l10n_py_edi_log.py

from odoo import models, fields, api, _


class EDILog(models.Model):
    """Modelo para registrar logs de las operaciones EDI"""
    _name = 'l10n_py.edi.log'
    _description = 'EDI Operation Log'
    _order = 'timestamp desc'
    
    connector_id = fields.Many2one(
        'l10n_py.edi.connector.facturasend',
        string='Conector',
        ondelete='set null',
        help='Conector EDI utilizado'
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        ondelete='cascade'
    )
    
    method = fields.Selection([
        ('POST', 'POST'),
        ('GET', 'GET'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE')
    ], string='Método HTTP')
    
    endpoint = fields.Char('Endpoint')
    
    request_data = fields.Text('Datos Enviados')
    
    response_data = fields.Text('Respuesta')
    
    status_code = fields.Integer('Código de Estado')
    
    timestamp = fields.Datetime(
        'Fecha/Hora',
        default=fields.Datetime.now,
        required=True
    )
    
    error = fields.Boolean(
        'Es Error',
        compute='_compute_error',
        store=True
    )
    
    error_message = fields.Text('Mensaje de Error')
    
    @api.depends('status_code')
    def _compute_error(self):
        for record in self:
            record.error = record.status_code >= 400 if record.status_code else False

