- This module depends transitively on Enterprise: `l10n_py_account_batch_payment`
  (this module's direct dependency) itself depends on `account_batch_payment`,
  which is an Odoo **Enterprise** module (license `OEEL-1`) in Odoo 18. This
  is a known limitation inherited from the foundation module, documented
  here again for visibility: this module cannot be installed or used on a
  pure Community Odoo 18 instance without that Enterprise module (available
  in the KMEE environment via `erplivre-odoo`).
- **Generic schema, not a guaranteed-accepted format**: this exporter
  implements the ISO 20022 `pain.001.001.09` schema in its generic form.
  Whether a specific Paraguayan bank (or Bancard) accepts this exact XML
  layout has **not** been confirmed. This is **not** a universal format
  automatically accepted by any Paraguayan home banking; confirm with the
  receiving bank before using in production.
- **SPI/LBTR threshold is a placeholder**: the default value of the
  `l10n_py_iso20022_spi_lbtr_threshold` company field is not an
  authoritative figure from the BCP. It must be confirmed with the BCP
  before this classification can be trusted in production.
- **No XSD validation against the official schema**: the automated tests
  validate the generated XML's structure using `lxml` assertions (presence
  of `GrpHdr`, `PmtInf`, `CdtTrfTxInf`, and consistency of `NbOfTxs`/
  `CtrlSum`), but do **not** validate it against the official
  `pain.001.001.09` XSD published at https://www.iso20022.org. The
  automated test environment used during development had no internet
  access to download that XSD, and no XSD was vendorized/fabricated as a
  substitute (a fake XSD would give a false sense of formal validation).
  This is a known, documented limitation: perform a real XSD validation
  (and, ideally, a validation round-trip with the receiving bank) before
  using this exporter in production.
