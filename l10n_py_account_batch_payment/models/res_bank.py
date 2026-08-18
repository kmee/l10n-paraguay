# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResBank(models.Model):
    _inherit = "res.bank"

    l10n_py_sipap_bank_code = fields.Char(
        string="Código de Banco SIPAP",
        help="Código de banco asignado por el Banco Central del Paraguay "
        "(BCP) para el Sistema de Pagos (SIPAP). Requerido para poder "
        "identificar el banco destino en un archivo de pago por lote.",
    )
    l10n_py_sipap_export_code = fields.Char(
        string="Formato de Exportación SIPAP",
        help="Código técnico del generador de archivo de lote SIPAP a "
        "usar para este banco (por ejemplo 'iso20022'). Se resuelve, en "
        "tiempo de generación del archivo, contra los métodos "
        "'_l10n_py_generate_batch_file_<code>' que los módulos "
        "exportadores instalados registren en account.payment.order. "
        "Dejar vacío si el banco no tiene un exportador implementado "
        "todavía: la generación del archivo fallará entonces con un "
        "mensaje de error explícito, en lugar de producir un archivo "
        "en un formato no confirmado.",
    )
