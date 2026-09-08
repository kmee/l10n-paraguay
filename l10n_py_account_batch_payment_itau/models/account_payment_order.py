# Copyright 2026 KMEE
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, models
from odoo.exceptions import UserError


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _l10n_py_dispatch_batch_api_itau(self):
        """Registered as the API-dispatch handler for
        ``res.bank.l10n_py_sipap_export_code = "itau"`` +
        ``l10n_py_sipap_export_mode = "api"`` (resolved by
        ``l10n_py_account_batch_payment``'s
        ``_l10n_py_generate_batch_file``, same mechanism used by
        ``l10n_py_account_batch_payment_atlas``'s
        ``_l10n_py_dispatch_batch_api_atlas``).

        Deliberately NOT implemented yet: Banco Itaú's Payments Platform
        API (endpoint, request/response schema, whether it is
        synchronous or requires polling like Banco Atlas's) is only
        documented inside the bank's own developer portal, gated behind
        completing the digital subscription to the Open Banking channel
        -- see ``l10n_py_account_payment_itau``'s known gap and the
        elm-template plan at
        ``docs/superpowers/plans/2026-09-08-itau-py-open-banking-
        integracao.md`` (Fase 3).

        This method exists now so the *plug-in mechanism itself*
        (configuring a bank with ``export_code="itau"``/
        ``export_mode="api"`` and having ``generate_payment_file``
        resolve to this handler, with no changes needed in the core
        module) is proven end-to-end today, without pretending the real
        bank call already works. Raises a clear, actionable error instead
        of silently doing nothing or fabricating a fake success.
        """
        self.ensure_one()
        raise UserError(
            _(
                "La integración real con la API Payments Platform del "
                "Banco Itaú Open Banking todavía no está implementada "
                "(Fase 3 del plan, pendiente de la documentación técnica "
                "del banco, liberada solo después de completar la "
                "suscripción al canal). El mecanismo de configuración "
                "(banco '%(bank)s' -> exportador 'itau') ya está "
                "correctamente resuelto -- lo que falta es la llamada "
                "real a la API.",
                bank=self.company_partner_bank_id.bank_id.display_name,
            )
        )
