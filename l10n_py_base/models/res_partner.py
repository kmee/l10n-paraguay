# l10n_py_base/models/res_partner.py

from odoo import api, fields, models

from ..validators.ruc_validator import RUCValidator


class ResPartner(models.Model):
    """Extensión de res.partner para Paraguay con campos fiscales"""

    _inherit = "res.partner"

    # ============== CAMPOS FISCALES PY ==============

    l10n_py_ruc = fields.Char(
        string="RUC",
        size=20,
        help="Registro Único del Contribuyente (sin dígito verificador)",
    )

    l10n_py_ruc_dv = fields.Char(
        string="DV",
        size=1,
        compute="_compute_ruc_dv",
        store=True,
        help="Dígito verificador del RUC",
    )

    l10n_py_taxpayer_type = fields.Selection(
        [
            ("1", "Contribuyente"),
            ("2", "No Contribuyente"),
        ],
        string="Tipo de Contribuyente",
        help="Tipo de contribuyente según la SET",
    )

    l10n_py_fantasy_name = fields.Char(
        string="Nombre de Fantasía",
        help="Nombre comercial o de fantasía",
    )

    l10n_py_activity_description = fields.Char(
        string="Actividad Económica",
        help="Descripción de la actividad económica principal",
    )

    # ============== CAMPOS DE UBICACIÓN (RELATED) ==============

    l10n_py_department_code = fields.Integer(
        string="Código Departamento SET",
        related="state_id.l10n_py_code",
        store=True,
        readonly=True,
        help="Código del departamento según SET",
    )

    l10n_py_city_code = fields.Char(
        string="Código Ciudad SET",
        related="city_id.l10n_py_code",
        store=True,
        readonly=True,
        help="Código de la ciudad según SET",
    )

    # ============== CAMPOS BARRIO ==============

    l10n_py_neighborhood_id = fields.Many2one(
        comodel_name="l10n_py.neighborhood",
        string="Barrio",
        domain="[('city_id', '=', city_id)]",
        help="Barrio o distrito del contacto",
    )

    l10n_py_neighborhood_name = fields.Char(
        string="Nombre del Barrio",
        related="l10n_py_neighborhood_id.name",
        store=True,
        readonly=True,
    )

    # ============== COMPUTE METHODS ==============

    @api.depends("l10n_py_ruc")
    def _compute_ruc_dv(self):
        """Calcular dígito verificador del RUC"""
        for partner in self:
            if partner.l10n_py_ruc:
                partner.l10n_py_ruc_dv = RUCValidator.get_check_digit(
                    partner.l10n_py_ruc
                )
            else:
                partner.l10n_py_ruc_dv = False

    # ============== ONCHANGE METHODS ==============

    @api.onchange("l10n_py_neighborhood_id")
    def _onchange_l10n_py_neighborhood_id(self):
        """Actualizar ciudad y código postal cuando cambia el barrio"""
        if self.l10n_py_neighborhood_id:
            if not self.city_id:
                self.city_id = self.l10n_py_neighborhood_id.city_id
            if not self.zip and self.l10n_py_neighborhood_id.zipcode:
                self.zip = self.l10n_py_neighborhood_id.zipcode

    @api.onchange("city_id")
    def _onchange_city_id(self):
        """Limpiar barrio si cambia la ciudad y no coincide"""
        if (
            self.l10n_py_neighborhood_id
            and self.city_id
            and self.l10n_py_neighborhood_id.city_id != self.city_id
        ):
            self.l10n_py_neighborhood_id = False

    @api.model
    def _formatting_address_fields(self):
        """Returns the list of address fields usable to format addresses."""
        return super()._formatting_address_fields() + ["l10n_py_neighborhood_name"]
