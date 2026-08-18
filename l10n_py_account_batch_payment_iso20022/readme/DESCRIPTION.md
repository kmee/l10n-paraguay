This module adds a **generic ISO 20022 (pain.001.001.09)** exporter to the
pluggable SIPAP batch payment framework provided by
`l10n_py_account_batch_payment`, for the Paraguayan SIPAP (Sistema de Pagos
Paraguay) interbank system.

**IMPORTANT — read before using in production**: this exporter implements
the **generic** ISO 20022 `pain.001.001.09` schema. It is **not** a format
guaranteed to be accepted by any specific Paraguayan home banking or by
Bancard as-is. Acceptance of this exact layout by a given bank **must be
confirmed with that bank** before using it in production. This is not a
universal format automatically accepted by every Paraguayan bank.

It registers the technical code `iso20022` on
`res.bank.l10n_py_batch_export_code` (see `l10n_py_account_batch_payment`)
and implements `_l10n_py_export_iso20022()` on `account.batch.payment`,
following the plugin contract defined by that foundation module.

Additionally, the generated file distinguishes between the two SIPAP
settlement channels defined by the BCP:

- **SPI** (Sistema de Pagos Inmediatos): low-value transfers.
- **LBTR** (Liquidación Bruta en Tiempo Real): high-value transfers, or any
  transfer in a currency other than the company's currency.

This distinction is reported in `PmtTpInf/CtgyPurp/Prtry` of each `PmtInf`
block. **The monetary threshold that separates SPI from LBTR is not
hardcoded**: it is read from a per-company configuration field (see
CONFIGURE section) whose default value is only a placeholder — **the real
threshold must be confirmed with the BCP**.
