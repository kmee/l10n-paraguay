# l10n_py_base/models/l10n_py_district.py

from odoo import fields, models


class District(models.Model):
    """Distritos de Paraguay (nivel intermedio entre departamento y ciudad)"""

    _name = "l10n_py.district"
    _description = "Distrito de Paraguay"
    _order = "code"

    code = fields.Integer(string="Código SET", required=True)
    name = fields.Char(string="Nombre", required=True, translate=True)
    state_id = fields.Many2one(
        "res.country.state",
        string="Departamento",
        domain="[('country_id.code', '=', 'PY')]",
        required=True,
        help="Departamento al que pertenece el distrito",
    )
    country_id = fields.Many2one(
        "res.country",
        related="state_id.country_id",
        string="País",
        store=True,
        readonly=True,
    )
    city_ids = fields.One2many(
        "res.city",
        "l10n_py_district_id",
        string="Ciudades",
        help="Ciudades que pertenecen a este distrito",
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "El código del distrito debe ser único")
    ]

    def name_get(self):
        """Mostrar nombre con departamento"""
        result = []
        for district in self:
            name = district.name
            if district.state_id:
                name = f"{name} ({district.state_id.name})"
            result.append((district.id, name))
        return result
