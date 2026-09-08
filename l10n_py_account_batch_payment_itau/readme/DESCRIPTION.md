Registers Banco Itaú Open Banking as a valid, API-mode SIPAP batch export
target in ``account.payment.order`` (using
``l10n_py_account_batch_payment``'s generic dispatch resolution -- no
core changes needed), sharing credentials/transport with
``l10n_py_account_payment_itau``.

**This module's dispatch method is a deliberate stub.** It proves the
plug-in mechanism (bank configured with ``export_code="itau"`` +
``export_mode="api"`` correctly resolves to this module's handler) but
raises a clear error instead of calling a real, unconfirmed API -- Banco
Itaú's technical API documentation (endpoints, schemas, sync vs. polling
behavior) is only released after completing the digital subscription to
the bank's Open Banking channel, which had not happened when this module
was created (2026-09-08). See
``docs/superpowers/plans/2026-09-08-itau-py-open-banking-integracao.md``
(elm-template repo) for the phased plan -- this module covers Fases 1-2
only; Fase 3 replaces the stub with the real call.
