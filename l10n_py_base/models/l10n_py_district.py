# -*- coding: utf-8 -*-
# l10n_py_base/models/l10n_py_district.py

from odoo import models, fields


class District(models.Model):
    """Distritos de Paraguay"""
    _name = 'l10n_py.district'
    _description = 'Distrito de Paraguay'
    _order = 'code'

    code = fields.Integer(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True, translate=True)
    department_id = fields.Many2one('l10n_py.department', string='Departamento')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código del distrito debe ser único')
    ]

