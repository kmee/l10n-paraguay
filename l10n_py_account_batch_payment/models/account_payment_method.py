# l10n_py_account_batch_payment/models/account_payment_method.py

from odoo import api, models

# Código determinístico del método de pago SIPAP Batch File. Se define una
# única vez aquí y se reutiliza en account_batch_payment.py y en el dato
# XML del método de pago (data/account_payment_method_data.xml) para no
# tener el string repetido/hardcodeado en distintos puntos del módulo.
L10N_PY_SIPAP_BATCH_FILE_CODE = "sipap_batch_file"


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        """Registra el método de pago "SIPAP Batch File".

        Sigue el mismo patrón que usa el core de Odoo/OCA para registrar
        nuevos métodos de pago de lote (ver por ejemplo `account_sepa`,
        que registra `sepa_ct` de la misma forma). El registro real del
        `account.payment.method` (nombre, código, tipo) se hace vía dato
        XML en `data/account_payment_method_data.xml`; este método solo
        informa a `account.payment.method` en qué diarios (`domain`) el
        método debe estar disponible.
        """
        res = super()._get_payment_method_information()
        res[L10N_PY_SIPAP_BATCH_FILE_CODE] = {
            "mode": "unique",
            "domain": [("type", "=", "bank")],
        }
        return res
