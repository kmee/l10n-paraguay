# l10n_py_edi_base/models/l10n_py_number_inutilization.py

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

MAX_INUTILIZATION_RANGE = 1000


class NumberInutilization(models.Model):
    """Inutilización de números de documentos electrónicos.

    Permite inutilizar rangos de números que no serán usados,
    comunicando al SIFEN para mantener la secuencia consistente.
    """

    _name = "l10n_py.number.inutilization"
    _description = "Inutilización de Números"
    _order = "create_date desc"

    authorization_id = fields.Many2one(
        "account.authorization",
        string="Timbrado",
        required=True,
        ondelete="restrict",
    )

    number_from = fields.Integer(
        string="Número Desde",
        required=True,
    )

    number_to = fields.Integer(
        string="Número Hasta",
        required=True,
    )

    motive = fields.Text(
        string="Motivo",
        required=True,
    )

    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("sent", "Enviado"),
            ("accepted", "Aceptado"),
            ("rejected", "Rechazado"),
        ],
        string="Estado",
        default="draft",
        readonly=True,
    )

    company_id = fields.Many2one(
        related="authorization_id.company_id",
        store=True,
    )

    quantity = fields.Integer(
        string="Cantidad",
        compute="_compute_quantity",
    )

    def _compute_quantity(self):
        for rec in self:
            rec.quantity = rec.number_to - rec.number_from + 1

    # ============== CONSTRAINTS ==============

    @api.constrains("number_from", "number_to")
    def _check_range(self):
        for rec in self:
            if rec.number_from <= 0 or rec.number_to <= 0:
                raise ValidationError(_("Los números deben ser mayores a cero."))
            if rec.number_to < rec.number_from:
                raise ValidationError(
                    _("El número final debe ser mayor o igual al inicial.")
                )
            quantity = rec.number_to - rec.number_from + 1
            if quantity > MAX_INUTILIZATION_RANGE:
                raise ValidationError(
                    _(
                        "El rango máximo de inutilización es "
                        "%(max)s números (solicitados: %(qty)s).",
                        max=MAX_INUTILIZATION_RANGE,
                        qty=quantity,
                    )
                )

    @api.constrains("number_from", "number_to", "authorization_id")
    def _check_within_authorization_range(self):
        """Verificar que la faja está dentro del rango del timbrado."""
        for rec in self:
            auth = rec.authorization_id
            if rec.number_from < auth.invoice_number_from:
                raise ValidationError(
                    _(
                        "El número inicial está fuera del rango "
                        "del timbrado (mínimo: %(min)s).",
                        min=auth.invoice_number_from,
                    )
                )
            if rec.number_to > auth.invoice_number_to:
                raise ValidationError(
                    _(
                        "El número final está fuera del rango "
                        "del timbrado (máximo: %(max)s).",
                        max=auth.invoice_number_to,
                    )
                )

    @api.constrains("number_from", "number_to", "authorization_id")
    def _check_no_used_numbers(self):
        """Verificar que ningún número de la faja ya fue usado."""
        for rec in self:
            used = self.env["account.move"].search_count(
                [
                    ("l10n_py_authorization_id", "=", rec.authorization_id.id),
                    ("l10n_py_invoice_number", ">=", rec.number_from),
                    ("l10n_py_invoice_number", "<=", rec.number_to),
                    ("state", "=", "posted"),
                ]
            )
            if used:
                raise ValidationError(
                    _(
                        "Hay %(count)s número(s) en el rango que "
                        "ya fueron usados en facturas confirmadas.",
                        count=used,
                    )
                )
