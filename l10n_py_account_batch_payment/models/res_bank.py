# l10n_py_account_batch_payment/models/res_bank.py

from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    l10n_py_sipap_code = fields.Char(
        string="Código SIPAP",
        help="Código numérico del banco en el Sistema de Pagos Paraguay "
        "(SIPAP) administrado por el BCP. Se utiliza para completar el "
        "archivo de lote enviado a Bancard, no debe confundirse con el "
        "código de exportación (formato) del archivo.",
    )

    # Selection vacío a propósito: este módulo es solo el framework y no
    # implementa ningún formato de archivo. Cada módulo "exportador de
    # banco" (ej. un módulo ISO 20022, o un módulo propietario de un banco
    # específico) debe extender este selection vía `selection_add` con su
    # propio código, e implementar un método `_l10n_py_export_<codigo>` en
    # `account.batch.payment` (ver `account_batch_payment.py`).
    l10n_py_batch_export_code = fields.Selection(
        selection=[],
        string="Formato de Exportación de Lote SIPAP",
        help="Determina qué exportador (módulo) genera el archivo de lote "
        "SIPAP para pagos dirigidos a este banco. Vacío si ningún módulo "
        "exportador fue instalado para este banco.",
    )
