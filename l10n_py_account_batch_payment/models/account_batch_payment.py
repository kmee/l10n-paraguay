# l10n_py_account_batch_payment/models/account_batch_payment.py

from odoo import _, models
from odoo.exceptions import UserError

from .account_payment_method import L10N_PY_SIPAP_BATCH_FILE_CODE


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def _get_methods_generating_files(self):
        # Habilita el botón "Generar Archivo" (en lugar de "Imprimir") en
        # los lotes que usan el método de pago SIPAP Batch File.
        res = super()._get_methods_generating_files()
        res.append(L10N_PY_SIPAP_BATCH_FILE_CODE)
        return res

    def _generate_export_file(self):
        # Punto de enganche estándar de Odoo/OCA (usado también por
        # `account_sepa`, `l10n_au_aba`, etc.) para generar el archivo de
        # un lote. Delegamos en nuestro propio framework plugable cuando
        # el método de pago del lote es el de SIPAP.
        if self.payment_method_code == L10N_PY_SIPAP_BATCH_FILE_CODE:
            return self._l10n_py_generate_batch_file()
        return super()._generate_export_file()

    def _l10n_py_get_batch_export_bank(self):
        """Banco de referencia usado para resolver el exportador SIPAP.

        Decisión de diseño: se usa el banco de la cuenta bancaria del
        DIARIO (es decir, el banco/canal por el cual la empresa envía el
        lote), y no el banco de cada beneficiario individual.

        Motivo: un mismo lote SIPAP puede incluir pagos a beneficiarios de
        bancos distintos, pero el *formato* del archivo exportado depende
        de a qué banco/canal se envía el lote completo (por ejemplo, el
        banco que procesa el archivo por cuenta de la empresa pagadora),
        no del banco de cada beneficiario particular. Resolver el
        exportador por beneficiario sería ambiguo (o forzaría a partir un
        único lote en varios archivos sin que la especificación lo pida).
        """
        self.ensure_one()
        bank_account = self.journal_id.bank_account_id
        return bank_account.bank_id if bank_account else self.env["res.bank"]

    def _l10n_py_generate_batch_file(self):
        """Framework plugable de exportación de lote SIPAP.

        Este método NO implementa ningún formato de archivo concreto (ni
        ISO 20022 ni un formato propietario de un banco). Resuelve, a
        partir del banco de referencia del lote (ver
        `_l10n_py_get_batch_export_bank`), qué "exportador de banco" debe
        generar el archivo y delega en él.

        Mecanismo de extensión (selection extensible + dispatch por
        nombre de método, el mismo patrón ya usado en Odoo/OCA para
        "tipos" extensibles por herencia, por ejemplo
        `delivery.carrier.delivery_type`): cada módulo exportador debe

        1. Agregar su propio código al selection
           `res.bank.l10n_py_batch_export_code` vía `selection_add`.
        2. Implementar, en este mismo modelo (`account.batch.payment`),
           un método `_l10n_py_export_<codigo>(self)` que retorne un
           diccionario `{'file': <base64>, 'filename': <str>}`, exactamente
           el mismo contrato que usa el `_generate_export_file()` nativo
           de `account_batch_payment`.

        Este módulo (framework) nunca conoce los exportadores concretos:
        el primero en registrarse será el módulo ISO 20022 (dependiente de
        este), y luego podrán agregarse exportadores propietarios de
        bancos específicos sin modificar este archivo.
        """
        self.ensure_one()
        bank = self._l10n_py_get_batch_export_bank()
        export_code = bank.l10n_py_batch_export_code if bank else False
        if not export_code:
            raise UserError(
                _(
                    "No hay ningún exportador de lote SIPAP registrado "
                    "para el banco '%s'. Instale el módulo "
                    "correspondiente al formato requerido por este banco "
                    "(por ejemplo, el módulo de exportación ISO 20022) o "
                    "configure el formato de exportación en la ficha del "
                    "banco."
                )
                % (bank.name if bank else _("(sin banco configurado)"))
            )

        method_name = f"_l10n_py_export_{export_code}"
        exporter = getattr(self, method_name, None)
        if exporter is None:
            raise UserError(
                _(
                    "El banco '%(bank)s' está configurado con el formato "
                    "de exportación '%(code)s', pero no existe ningún "
                    "método '%(method)s' implementado. Verifique que el "
                    "módulo exportador correspondiente esté instalado "
                    "correctamente."
                )
                % {
                    "bank": bank.name,
                    "code": export_code,
                    "method": method_name,
                }
            )
        return exporter()
