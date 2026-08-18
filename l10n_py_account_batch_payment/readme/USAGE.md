1. Register the beneficiary's document (CI/RUC) and, if applicable, the
   CAS alias on the recipient's bank account (**Contacts > a partner >
   Bank Accounts**, or directly from **Accounting > Configuration >
   Bank Accounts**).
2. Make sure the bank used to submit the batch (the bank account linked
   to the journal) has both **Código SIPAP** and **Formato de
   Exportación de Lote SIPAP** configured (the second one requires a
   concrete exporter module to be installed, e.g. an ISO 20022 exporter).
3. Create outbound payments as usual, using the **SIPAP Batch File**
   payment method, and group them into a batch payment
   (**Accounting > Vendors > Batch Payments**, or from the payments list
   view).
4. Validate the batch. Since `SIPAP Batch File` is registered as a
   file-generating method, Odoo will offer **Generate File** instead of
   **Print**, and the export logic described in `CONFIGURE.md` will run.
5. If no exporter module is installed for the batch's bank, or the bank
   has no export format configured, a clear error is raised instead of
   generating an incomplete or empty file.
