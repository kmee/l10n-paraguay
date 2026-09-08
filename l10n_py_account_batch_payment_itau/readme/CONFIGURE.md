On the relevant ``res.bank`` record for Banco Itaú, set:

- Código de Banco SIPAP (``l10n_py_sipap_bank_code``): the BCP-assigned
  code for Itaú.
- Formato de Exportación SIPAP (``l10n_py_sipap_export_code``): ``itau``.
- Modo de Exportación SIPAP (``l10n_py_sipap_export_mode``): ``API
  directa``.

Then configure the company's bank account for Itaú Open Banking as
described in ``l10n_py_account_payment_itau``'s CONFIGURE.md.

With this configuration, ``account.payment.order.generate_payment_file()``
resolves to this module's ``_l10n_py_dispatch_batch_api_itau`` -- which,
as of this module's creation, raises a clear "not yet implemented"
error rather than calling a real API. See DESCRIPTION.md.
