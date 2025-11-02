# -*- coding: utf-8 -*-
# l10n_py_edi_base/models/res_company.py

from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    # ============== CAMPOS EDI PARAGUAY ==============
    
    l10n_py_ruc = fields.Char(
        string='RUC',
        size=8,
        help='Registro Único del Contribuyente sin dígito verificador'
    )
    
    l10n_py_dv = fields.Char(
        string='DV',
        size=1,
        compute='_compute_dv',
        store=True,
        help='Dígito Verificador del RUC'
    )
    
    l10n_py_ruc_full = fields.Char(
        string='RUC Completo',
        compute='_compute_ruc_full',
        store=True,
        help='RUC con dígito verificador'
    )
    
    l10n_py_trade_name = fields.Char(
        string='Nombre Fantasía',
        help='Nombre comercial o de fantasía de la empresa'
    )
    
    l10n_py_economic_activity = fields.Char(
        string='Actividad Económica',
        help='Código de actividad económica principal'
    )
    
    l10n_py_department_code = fields.Integer(
        string='Código Departamento',
        help='Código del departamento según SET'
    )
    
    l10n_py_department_name = fields.Char(
        string='Departamento',
        related='partner_id.state_id.name',
        store=True
    )
    
    l10n_py_district_code = fields.Integer(
        string='Código Distrito',
        help='Código del distrito según SET'
    )
    
    l10n_py_city_code = fields.Integer(
        string='Código Ciudad',
        help='Código de la ciudad según SET'
    )
    
    # ============== COMPUTE METHODS ==============
    
    @api.depends('l10n_py_ruc')
    def _compute_dv(self):
        """Calcular dígito verificador del RUC"""
        for company in self:
            if company.l10n_py_ruc:
                company.l10n_py_dv = self._calculate_dv(company.l10n_py_ruc)
            else:
                company.l10n_py_dv = False
    
    @api.depends('l10n_py_ruc', 'l10n_py_dv')
    def _compute_ruc_full(self):
        """Calcular RUC completo con DV"""
        for company in self:
            if company.l10n_py_ruc and company.l10n_py_dv:
                company.l10n_py_ruc_full = f"{company.l10n_py_ruc}-{company.l10n_py_dv}"
            else:
                company.l10n_py_ruc_full = False
    
    # ============== PRIVATE METHODS ==============
    
    @staticmethod
    def _calculate_dv(ruc):
        """Calcular dígito verificador del RUC paraguayo"""
        if not ruc or not ruc.isdigit():
            return False
        
        ruc = ruc.replace('-', '').strip()
        
        if len(ruc) < 6:
            return False
        
        base_max = 11
        k = 2
        total = 0
        
        for digit in reversed(ruc):
            total += int(digit) * k
            k += 1
            if k > base_max:
                k = 2
        
        remainder = total % base_max
        
        if remainder > 1:
            dv = base_max - remainder
        else:
            dv = 0
        
        return str(dv)

