# l10n_py_base/models/res_city.py

from odoo import fields, models


class City(models.Model):
    """Extensión de res.city para Paraguay con distrito y código SET"""

    _inherit = "res.city"

    l10n_py_code = fields.Integer(
        string="Código SET",
        help="Código de la ciudad según SET (Subsecretaría de Estado de Tributación)",
    )

    l10n_py_district_id = fields.Many2one(
        "l10n_py.district",
        string="Distrito",
        help=(
            "Distrito al que pertenece la ciudad "
            "(nivel intermedio entre departamento y ciudad)"
        ),
    )

    _sql_constraints = [
        (
            "l10n_py_code_unique",
            "unique(l10n_py_code, country_id)",
            "El código SET de la ciudad debe ser único por país",
        )
    ]
