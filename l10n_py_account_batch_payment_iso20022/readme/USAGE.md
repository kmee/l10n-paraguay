Once configured (see CONFIGURE), generating a SIPAP batch file follows the
same flow described in `l10n_py_account_batch_payment`'s README: create
outbound payments with the **SIPAP Batch File** payment method, group them
into a batch payment, and use **Generate File**. If the batch's journal
bank has **ISO 20022 (pain.001.001.09, genérico)** configured as its
export format, this module's exporter runs and produces a
`pain.001.001.09` XML file (`CstmrCdtTrfInitn` with one `GrpHdr`, one
`PmtInf`, and one `CdtTrfTxInf` per payment in the batch).

Remember: **validate the generated file with the receiving bank before
using it in production.** This module implements the generic ISO 20022
schema; it does not guarantee acceptance by any specific Paraguayan bank.
