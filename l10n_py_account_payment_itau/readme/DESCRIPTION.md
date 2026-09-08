mTLS-authenticated REST client and per-bank-account credential storage
for Banco Itaú Paraguay's Open Banking channel (IOB): Business Account,
Account Statements, Payments Platform, Transfer Information and API
Toolbox.

This module implements no payment dispatch or reconciliation by itself
-- it is the shared transport layer used by
``l10n_py_account_batch_payment_itau``.

KNOWN GAP (documented, not an oversight): Itaú only publishes the real
endpoint paths, request/response schemas, and full authentication
details (beyond the mTLS handshake itself) inside its own developer
portal, gated behind completing the digital subscription to the Open
Banking channel. Nobody had that access when this module was created
(2026-09-08) -- see ``docs/pendencias-sipap-bancard.md`` in this repo and
the elm-template plan at
``docs/superpowers/plans/2026-09-08-itau-py-open-banking-integracao.md``.
Consequently ``ItauApiClient`` exposes no endpoint-specific methods yet
(contrast with ``l10n_py_account_payment_atlas``'s ``AtlasApiClient``,
which has confirmed, bank-documented methods) -- adding those before the
real documentation exists would commit a guess as if it were confirmed
behavior. That work is Fase 3 of the plan above.
