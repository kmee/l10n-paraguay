This module has no user-facing action by itself: it is a shared
transport layer. Payment dispatch is provided by the sibling module
``l10n_py_account_batch_payment_itau``.

``ItauApiClient`` currently exposes only a generic, authenticated
``call(method, path, body)`` -- no endpoint-specific methods exist yet
(see this module's known gap in DESCRIPTION.md). Any code calling it
directly today is, by construction, calling an unconfirmed endpoint.
