1. On the bank master data (`res.bank`) of the bank used to submit the
   SIPAP batch (i.e. the bank of the journal's bank account), set
   **Formato de Exportación de Lote SIPAP** to **ISO 20022 (pain.001.001.09,
   genérico)**. This is provided by
   `l10n_py_account_batch_payment`; installing this module simply adds
   this option to that selection field.
2. On **Settings > Companies**, configure the **Umbral SPI/LBTR (ISO 20022
   SIPAP)** field (`l10n_py_iso20022_spi_lbtr_threshold`), in the
   company's currency. Any batch whose total amount reaches this
   threshold, or that involves a payment in a currency other than the
   company's currency, is reported as **LBTR** in the exported file;
   otherwise it is reported as **SPI**.

   **This field ships with a placeholder default value. It is NOT an
   authoritative BCP figure.** The real SPI/LBTR cutoff must be confirmed
   with the BCP (Banco Central del Paraguay) and/or with the bank
   operating the SIPAP channel before relying on this classification in
   production. A per-company field was chosen (instead of a global
   `ir.config_parameter`) because this is fundamentally a business
   parameter that can vary by company/banking agreement, consistent with
   how other Paraguayan localization parameters are modeled as
   `res.company` fields in this repository (see `l10n_py_account`).
