This module adds the beneficiary data and the pluggable export framework
needed to generate batch payment files for the Paraguayan SIPAP
(Sistema de Pagos Paraguay) interbank system, as required by Bancard and
Paraguayan banks.

It is a **foundation module**: it does not implement any concrete file
format by itself. It provides:

- The beneficiary fields (CI/RUC document, CAS alias) required by the
  SIPAP batch file layout, stored on the bank account
  (`res.partner.bank`) that receives the payment.
- A `SIPAP Batch File` payment method (`account.payment.method`),
  registered following the same pattern used by Odoo/OCA modules such as
  `account_sepa`.
- A pluggable dispatch mechanism on `account.batch.payment` that resolves,
  per bank, which installed module should generate the actual export
  file, raising a clear error when no such module is installed.

Concrete exporters (for example, an ISO 20022 exporter, or a
bank-specific proprietary format) are implemented by other modules that
depend on this one.
