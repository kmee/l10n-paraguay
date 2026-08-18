# l10n_py_account_batch_payment_iso20022/models/res_bank.py

from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    # Registra este módulo como exportador del código "iso20022" en el
    # selection extensible definido (vacío) por l10n_py_account_batch_payment.
    # El método `_l10n_py_export_iso20022` correspondiente se implementa en
    # account_batch_payment.py.
    l10n_py_batch_export_code = fields.Selection(
        selection_add=[("iso20022", "ISO 20022 (pain.001.001.09, genérico)")],
        # "cascade" (no un default de fallback): si este módulo se
        # desinstala, los bancos que tenían "iso20022" configurado deben
        # quedar sin exportador (selection vacía), no migrar en silencio a
        # otro valor arbitrario, ya que no hay un exportador "por defecto"
        # razonable en el módulo base (framework).
        ondelete={"iso20022": "cascade"},
    )
