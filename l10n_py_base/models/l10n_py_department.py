# -*- coding: utf-8 -*-
# l10n_py_base/models/l10n_py_department.py

from odoo import models, fields


class Department(models.Model):
    """Departamentos de Paraguay"""
    _name = 'l10n_py.department'
    _description = 'Departamento de Paraguay'
    _order = 'code'

    code = fields.Integer(string='Código', required=True)
    name = fields.Char(string='Nombre', required=True, translate=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código del departamento debe ser único')
    ]

