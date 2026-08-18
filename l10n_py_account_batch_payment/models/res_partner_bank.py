# l10n_py_account_batch_payment/models/res_partner_bank.py

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Decisión de modelado: el tipo/número de documento y el alias CAS se
# guardan en `res.partner.bank` (la cuenta bancaria beneficiaria) y no en
# `res.partner`. Motivo: el archivo de lote SIPAP identifica al titular de
# la CUENTA BANCARIA puntual que recibe la transferencia, y ese titular
# puede no coincidir con la identificación fiscal principal del partner
# (ej. un partner con RUC empresarial puede tener una cuenta bancaria
# registrada a nombre de una persona física con CI). Modelar estos campos
# por cuenta bancaria evita ambigüedad cuando un mismo partner tiene varias
# cuentas con distintos titulares registrados ante el banco.
L10N_PY_DOCUMENT_TYPE_SELECTION = [
    ("ci", "CI - Cédula de Identidad"),
    ("ruc", "RUC - Registro Único del Contribuyente"),
]

L10N_PY_CAS_ALIAS_TYPE_SELECTION = [
    ("phone", "Teléfono"),
    ("email", "Email"),
    ("ruc", "RUC"),
    ("ci", "CI"),
]


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    l10n_py_document_type = fields.Selection(
        selection=L10N_PY_DOCUMENT_TYPE_SELECTION,
        string="Tipo de Documento (Beneficiario SIPAP)",
        help="Tipo de documento del titular de esta cuenta bancaria, "
        "requerido para completar el archivo de lote SIPAP.",
    )
    l10n_py_document_number = fields.Char(
        string="Número de Documento (Beneficiario SIPAP)",
        help="Número de CI o RUC del titular de esta cuenta bancaria.",
    )
    l10n_py_cas_alias_type = fields.Selection(
        selection=L10N_PY_CAS_ALIAS_TYPE_SELECTION,
        string="Tipo de Alias CAS",
        help="Tipo de alias del Catálogo de Alias SIPAP (CAS), usado por "
        "los bancos paraguayos para identificar cuentas destino en "
        "transferencias interbancarias sin necesidad del número de "
        "cuenta completo.",
    )
    l10n_py_cas_alias_value = fields.Char(
        string="Alias CAS",
        help="Valor del alias CAS (número de teléfono, email, RUC o CI, "
        "según el tipo seleccionado).",
    )

    @api.constrains("l10n_py_document_type", "l10n_py_document_number")
    def _check_l10n_py_document(self):
        for bank in self:
            if bool(bank.l10n_py_document_type) != bool(bank.l10n_py_document_number):
                raise ValidationError(
                    _(
                        "En la cuenta bancaria '%s', el tipo y el número de "
                        "documento del beneficiario SIPAP deben "
                        "completarse juntos."
                    )
                    % bank.display_name
                )

    @api.constrains("l10n_py_cas_alias_type", "l10n_py_cas_alias_value")
    def _check_l10n_py_cas_alias(self):
        for bank in self:
            if bool(bank.l10n_py_cas_alias_type) != bool(bank.l10n_py_cas_alias_value):
                raise ValidationError(
                    _(
                        "En la cuenta bancaria '%s', el tipo y el valor "
                        "del alias CAS deben completarse juntos."
                    )
                    % bank.display_name
                )
