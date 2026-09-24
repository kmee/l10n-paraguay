"""Post-init hook: dispara la carga de demo data PY DESPUÉS de que los
partners/products del propio módulo se hayan creado.

El método ``account.chart.template._create_demo_data()`` se ejecuta
originalmente durante ``try_loading``, que corre al instalar ``l10n_py``.
En ese momento ``l10n_py_account`` aún no existe en el sistema, así que
los xmlids ``l10n_py_account.partner_*`` y ``l10n_py_account.product_*``
no pueden ser resueltos. Aquí lo invocamos de nuevo, cuando ya están.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    account_module = env.ref("base.module_account", raise_if_not_found=False)
    if not account_module or not account_module.demo:
        _logger.info(
            "l10n_py_account demo: módulo account sin demo, skip."
        )
        return
    py_template = env.ref(
        "l10n_py.py_chart_template", raise_if_not_found=False
    )
    if not py_template:
        return
    companies = env["res.company"].search(
        [("chart_template_id", "=", py_template.id)]
    )
    if not companies:
        _logger.info(
            "l10n_py_account demo: sin empresas con chart PY, skip."
        )
        return
    # Diagnostico: estado de l10n_py_account en este momento
    self_mod = env["ir.module.module"].search(
        [("name", "=", "l10n_py_account")], limit=1
    )
    _logger.info(
        "l10n_py_account demo: module state = %s", self_mod.state
    )

    for company in companies:
        _logger.info(
            "l10n_py_account demo: generando datos demo para %s",
            company.name,
        )
        template_c = py_template.with_company(company).with_context(
            default_company_id=company.id,
            allowed_company_ids=[company.id],
        )
        try:
            template_c._create_demo_data()
        except Exception as e:  # noqa: BLE001
            _logger.exception(
                "l10n_py_account demo: error generando demo: %s", e
            )

    # Nota: la finalización (action_preview_xml + estados EDI + payments)
    # solo es posible cuando ``l10n_py_edi_base/sifen`` esté cargado. Como
    # ese módulo se carga DESPUÉS de ``l10n_py_account`` (no es dep), la
    # finalización se delega al ``post_init_hook`` de ``erplivre_l10n_py_account``
    # —que está al final del orden de instalación.
