# -*- coding: utf-8 -*-
# l10n_py_base/models/l10n_py_city.py

from odoo import models, fields


class City(models.Model):
    """Ciudades de Paraguay"""
    _name = 'l10n_py.city'
    _description = 'Ciudad de Paraguay'
    _order = 'code'

    code = fields.Integer(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True, translate=True)
    district_id = fields.Many2one('l10n_py.district', string='Distrito')

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código de la ciudad debe ser único')
    ]

