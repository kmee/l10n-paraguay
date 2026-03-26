# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_py_maquila_admission_id = fields.Many2one(
        "l10n_py.maquila.admission",
        string="Maquila Admission",
    )
    l10n_py_maquila_export_id = fields.Many2one(
        "l10n_py.maquila.export",
        string="Maquila Export",
    )
