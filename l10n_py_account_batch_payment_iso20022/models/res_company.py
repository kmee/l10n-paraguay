# l10n_py_account_batch_payment_iso20022/models/res_company.py

from odoo import fields, models

# Valor por defecto del umbral SPI/LBTR, en guaraníes (PYG).
#
# ADVERTENCIA: este valor es un PLACEHOLDER de configuración, no un dato
# autoritativo. El corte real que distingue una transferencia SPI (Sistema
# de Pagos Inmediatos, bajo valor) de una LBTR (Liquidación Bruta en Tiempo
# Real, alto valor / moneda extranjera) es definido por el BCP y puede
# variar. Debe confirmarse con el BCP y/o con el banco emisor del canal
# SIPAP antes de usar este exportador en producción; hasta entonces, cada
# empresa debe ajustar este valor manualmente según lo que le confirme su
# banco.
L10N_PY_ISO20022_SPI_LBTR_THRESHOLD_DEFAULT = 50_000_000


class ResCompany(models.Model):
    _inherit = "res.company"

    # Decisión de diseño: se modela como campo de `res.company` (no como
    # `ir.config_parameter` global) porque el umbral es, en principio, un
    # dato de negocio por empresa (cada empresa puede tener su propio
    # acuerdo/canal con su banco SIPAP), de la misma forma que otros
    # parámetros contables de la empresa se modelan como campos de
    # `res.company` en Odoo/OCA (ver por ejemplo los campos de
    # `l10n_py_account`). Un `ir.config_parameter` sería más apropiado si
    # el valor fuera puramente técnico/global sin variación posible por
    # empresa, que no es el caso aquí.
    l10n_py_iso20022_spi_lbtr_threshold = fields.Monetary(
        string="Umbral SPI/LBTR (ISO 20022 SIPAP)",
        currency_field="currency_id",
        default=L10N_PY_ISO20022_SPI_LBTR_THRESHOLD_DEFAULT,
        help="Monto (en la moneda de la empresa) a partir del cual una "
        "transferencia del lote SIPAP se clasifica como LBTR (Liquidación "
        "Bruta en Tiempo Real) en lugar de SPI (Sistema de Pagos "
        "Inmediatos) en el archivo ISO 20022 exportado. "
        "ADVERTENCIA: el valor por defecto es solo un placeholder de "
        "configuración; el corte real debe confirmarse con el BCP antes "
        "de usarse en producción.",
    )
