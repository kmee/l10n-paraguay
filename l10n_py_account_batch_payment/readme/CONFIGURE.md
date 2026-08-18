## Beneficiary data

For every bank account (`res.partner.bank`) that will receive SIPAP batch
payments, configure:

- **Tipo de Documento (Beneficiario SIPAP)** / **Número de Documento**:
  the CI or RUC of the actual holder of that specific bank account. This
  is stored on the bank account, not on the partner, because a partner's
  main fiscal identification (e.g. a company RUC) can differ from the
  document registered for a particular bank account (e.g. a personal CI).
- **Tipo de Alias CAS** / **Alias CAS**: the alias registered in the
  SIPAP Catálogo de Alias (phone, email, RUC or CI), when the beneficiary
  is identified by alias instead of (or in addition to) the full account
  number.

On the bank master data (`res.bank`), configure:

- **Código SIPAP**: the numeric bank code used inside the SIPAP batch
  file layout (a plain business value, unrelated to the plugin mechanism
  described below).
- **Formato de Exportación de Lote SIPAP**: the technical key used to
  select which installed module generates the batch file for that bank
  (see "Extension mechanism" below). Leave empty if no exporter module is
  installed yet for that bank; attempting to generate a file in that case
  raises a clear error instead of producing an empty/incorrect file.

## Payment method

Installing this module registers the **SIPAP Batch File** payment method
(`account.payment.method`, code `sipap_batch_file`, outbound only). Add
it to the payment method lines of the bank journal(s) used to submit
SIPAP batches, the same way any other outbound payment method is added
to a journal.

## Extension mechanism (for module authors)

This module intentionally does **not** implement any concrete file
format. The dispatch is a two-step, fully pluggable mechanism, following
the same "extensible selection + dispatch by method name" idiom already
used in Odoo/OCA for other extensible "types" (for example
`delivery.carrier.delivery_type`):

1. A module implementing a concrete SIPAP exporter (for instance an
   ISO 20022 exporter) must extend the selection field
   `res.bank.l10n_py_batch_export_code` via `selection_add`, adding its
   own technical code (e.g. `iso20022`).
2. That same module must implement, on `account.batch.payment`, a method
   named `_l10n_py_export_<code>` (e.g. `_l10n_py_export_iso20022`)
   returning a dict `{'file': <base64 content>, 'filename': <str>}` —
   exactly the same contract used by Odoo's native
   `_generate_export_file()` hook (see `account_sepa` for a reference
   implementation of that same native hook).

At runtime, `account.batch.payment._l10n_py_generate_batch_file()`:

1. Resolves the reference bank for the batch. This is the bank of the
   **journal's own bank account** (the channel through which the company
   submits the batch), not the bank of any individual beneficiary. A
   single SIPAP batch can include beneficiaries at different banks, but
   the file *format* required by the receiving/processing channel is a
   property of that channel, not of each beneficiary.
2. Reads `l10n_py_batch_export_code` from that bank.
3. Looks up and calls `_l10n_py_export_<code>` on `account.batch.payment`.
4. Raises a `UserError` if no code is configured, or if the code is
   configured but no matching method is implemented (i.e. no exporter
   module installed) — it never generates a silent/empty file.

This module never needs to know about concrete exporter modules: the
first one to register against it will be an ISO 20022 exporter module
that depends on this one.
